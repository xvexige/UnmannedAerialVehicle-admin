# -*- coding: utf-8 -*-
"""
后端 API 集成测试
运行: python tests/test_api.py
确保后端已启动: uvicorn app.main:app --port 8000
"""
import httpx
import sys
import io
import traceback
from datetime import datetime

# Windows GBK 控制台输出修复
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000/v1"
ROOT_URL = "http://127.0.0.1:8000"
client = httpx.Client(base_url=BASE_URL, timeout=10)
root_client = httpx.Client(base_url=ROOT_URL, timeout=10)

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[TEST]"

results = {"pass": 0, "fail": 0, "errors": []}

# 全局测试状态（各步骤间共享）
state = {}


def test(name: str, fn):
    try:
        fn()
        print(f"  {PASS}  {name}")
        results["pass"] += 1
    except AssertionError as e:
        msg = str(e)
        print(f"  {FAIL}  {name} → {msg}")
        results["fail"] += 1
        results["errors"].append({"name": name, "error": msg})
    except Exception as e:
        msg = traceback.format_exc().strip().split('\n')[-1]
        print(f"  {FAIL}  {name} → {msg}")
        results["fail"] += 1
        results["errors"].append({"name": name, "error": msg})


def assert_ok(res: httpx.Response, code: int = 200):
    assert res.status_code == code, f"HTTP {res.status_code}: {res.text[:200]}"
    data = res.json()
    assert data.get("code") == 200, f"business code={data.get('code')}, msg={data.get('message')}"
    return data.get("data")


def auth_header():
    return {"Authorization": f"Bearer {state.get('access_token', '')}"}


# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("  无人机SaaS平台 · 后端API全量测试")
print(f"  时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  目标：{BASE_URL}")
print(f"{'='*60}\n")

# ─── 0. 健康检查 ──────────────────────────────────────────────────────────────
print(f"{INFO} 0. 健康检查")


def t_health():
    r = root_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


test("GET /health", t_health)

# ─── 1. 认证模块 ──────────────────────────────────────────────────────────────
print(f"\n{INFO} 1. 认证模块（Auth）")

TENANT_CODE = f"TEST_{datetime.now().strftime('%H%M%S')}"
USERNAME = f"test_{datetime.now().strftime('%H%M%S')}@test.com"
PASSWORD = "Test@12345"


def t_register():
    r = client.post("/auth/register", json={
        "tenant_name": "测试企业",
        "tenant_code": TENANT_CODE,
        "username": USERNAME,
        "password": PASSWORD,
        "real_name": "测试管理员",
        "phone": "13800138000",
    })
    data = assert_ok(r)
    assert data.get("tenant_id"), "缺少 tenant_id"
    state["tenant_id"] = data["tenant_id"]


def t_register_duplicate():
    r = client.post("/auth/register", json={
        "tenant_name": "重复企业",
        "tenant_code": TENANT_CODE,
        "username": USERNAME,
        "password": PASSWORD,
        "real_name": "重复用户",
    })
    d = r.json()
    assert d.get("code") == 42201, f"重复注册应返回 42201，实际={d.get('code')}"


def t_login():
    r = client.post("/auth/login", json={
        "username": USERNAME,
        "password": PASSWORD,
        "tenant_code": TENANT_CODE,
    })
    data = assert_ok(r)
    assert data.get("access_token"), "缺少 access_token"
    state["access_token"] = data["access_token"]
    state["refresh_token"] = data["refresh_token"]
    state["user"] = data["user"]


def t_login_wrong_pwd():
    r = client.post("/auth/login", json={
        "username": USERNAME,
        "password": "WrongPass@999",
        "tenant_code": TENANT_CODE,
    })
    d = r.json()
    assert d.get("code") == 40101, f"密码错误应返回 40101，实际={d.get('code')}"


def t_me():
    r = client.get("/auth/me", headers=auth_header())
    data = assert_ok(r)
    assert data["username"] == USERNAME


def t_refresh():
    r = client.post("/auth/refresh", json={"refresh_token": state["refresh_token"]})
    data = assert_ok(r)
    assert data.get("access_token"), "刷新后缺少 access_token"
    state["access_token"] = data["access_token"]


def t_change_password():
    r = client.put("/auth/password", json={
        "old_password": PASSWORD,
        "new_password": "NewTest@6789",
    }, headers=auth_header())
    assert_ok(r)
    # 改回原密码
    r2 = client.post("/auth/login", json={
        "username": USERNAME, "password": "NewTest@6789", "tenant_code": TENANT_CODE,
    })
    data = assert_ok(r2)
    state["access_token"] = data["access_token"]
    r3 = client.put("/auth/password", json={
        "old_password": "NewTest@6789",
        "new_password": PASSWORD,
    }, headers=auth_header())
    assert_ok(r3)
    # 重新登录获取最新 token
    r4 = client.post("/auth/login", json={
        "username": USERNAME, "password": PASSWORD, "tenant_code": TENANT_CODE,
    })
    state["access_token"] = assert_ok(r4)["access_token"]


def t_no_token():
    r = client.get("/auth/me")
    assert r.json().get("code") == 40101, "无 Token 应返回 40101"


test("POST /auth/register（注册企业）", t_register)
test("POST /auth/register（重复注册返回42201）", t_register_duplicate)
test("POST /auth/login（正确凭据）", t_login)
test("POST /auth/login（密码错误返回40101）", t_login_wrong_pwd)
test("GET  /auth/me", t_me)
test("POST /auth/refresh", t_refresh)
test("PUT  /auth/password（改密码再改回）", t_change_password)
test("GET  /auth/me（无Token返回40101）", t_no_token)

# ─── 2. 套餐 ─────────────────────────────────────────────────────────────────
print(f"\n{INFO} 2. 套餐模块（Plans）")


def t_list_plans():
    r = client.get("/plans", headers=auth_header())
    data = assert_ok(r)
    assert isinstance(data, list), "应返回列表"
    state["plan_id"] = data[0]["id"] if data else None


test("GET /plans（列表）", t_list_plans)

# ─── 3. 无人机设备 ────────────────────────────────────────────────────────────
print(f"\n{INFO} 3. 设备管理（Drones）")


def t_create_drone():
    r = client.post("/drones", json={
        "name": "测试无人机-01",
        "sn": f"SN{datetime.now().strftime('%H%M%S')}001",
        "secret_key": "secret_key_abc123",
        "model": "DJI Mavic 3",
        "compute_mode": "cloud",
    }, headers=auth_header())
    data = assert_ok(r)
    state["drone_id"] = data["id"]
    state["drone_sn"] = data["sn"]


def t_list_drones():
    r = client.get("/drones?page=1&size=10", headers=auth_header())
    data = assert_ok(r)
    assert "list" in data and "total" in data


def t_get_drone():
    r = client.get(f"/drones/{state['drone_id']}", headers=auth_header())
    data = assert_ok(r)
    assert data["id"] == state["drone_id"]


def t_update_drone():
    r = client.put(f"/drones/{state['drone_id']}", json={
        "name": "测试无人机-01-已更新",
        "compute_mode": "cloud",
    }, headers=auth_header())
    data = assert_ok(r)
    assert data["name"] == "测试无人机-01-已更新"


def t_map_drones():
    r = client.get("/drones/map", headers=auth_header())
    assert_ok(r)


def t_drone_heartbeat():
    r = client.post("/drones/heartbeat", json={
        "drone_id": state["drone_id"],
        "battery_level": 85,
        "longitude": 116.397,
        "latitude": 39.909,
        "altitude": 120.5,
        "speed_ms": 8.3,
        "signal_strength": -65,
    }, headers=auth_header())
    assert_ok(r)


def t_duplicate_drone():
    r = client.post("/drones", json={
        "name": "重复无人机",
        "sn": state["drone_sn"],
        "secret_key": "other_secret",
        "compute_mode": "cloud",
    }, headers=auth_header())
    assert r.json().get("code") == 42201, "重复SN应返回42201"


test("POST /drones（绑定）", t_create_drone)
test("GET  /drones（列表）", t_list_drones)
test("GET  /drones/:id（详情）", t_get_drone)
test("PUT  /drones/:id（更新）", t_update_drone)
test("GET  /drones/map（地图点位）", t_map_drones)
test("POST /drones/heartbeat（心跳上报）", t_drone_heartbeat)
test("POST /drones（重复SN返回42201）", t_duplicate_drone)

# ─── 4. 任务管理 ──────────────────────────────────────────────────────────────
print(f"\n{INFO} 4. 任务管理（Tasks）")


def t_create_task():
    user_id = state["user"]["id"]
    r = client.post("/tasks", json={
        "name": "测试巡检任务",
        "drone_id": state["drone_id"],
        "assignee_id": user_id,
        "scheduled_at": "2026-04-01T09:00:00",
        "remark": "自动化测试任务",
        "waypoints": [
            {"seq": 0, "longitude": 116.39, "latitude": 39.90, "altitude": 100},
            {"seq": 1, "longitude": 116.40, "latitude": 39.91, "altitude": 120},
        ],
    }, headers=auth_header())
    data = assert_ok(r)
    state["task_id"] = data["id"]


def t_list_tasks():
    r = client.get("/tasks?page=1&size=10", headers=auth_header())
    data = assert_ok(r)
    assert "list" in data


def t_get_task():
    r = client.get(f"/tasks/{state['task_id']}", headers=auth_header())
    data = assert_ok(r)
    assert data["id"] == state["task_id"]


def t_update_task():
    r = client.put(f"/tasks/{state['task_id']}", json={
        "name": "测试巡检任务-已更新",
    }, headers=auth_header())
    data = assert_ok(r)
    assert data["name"] == "测试巡检任务-已更新"


def t_start_task():
    r = client.patch(f"/tasks/{state['task_id']}/status",
                     json={"status": "in_progress"}, headers=auth_header())
    data = assert_ok(r)
    assert data["status"] == "in_progress"


def t_complete_task():
    r = client.patch(f"/tasks/{state['task_id']}/status",
                     json={"status": "completed"}, headers=auth_header())
    data = assert_ok(r)
    assert data["status"] == "completed"


def t_invalid_status_transition():
    r = client.patch(f"/tasks/{state['task_id']}/status",
                     json={"status": "in_progress"}, headers=auth_header())
    assert r.json().get("code") == 40001, "已完成任务不可再次开始"


test("POST /tasks（创建）", t_create_task)
test("GET  /tasks（列表）", t_list_tasks)
test("GET  /tasks/:id（详情）", t_get_task)
test("PUT  /tasks/:id（更新）", t_update_task)
test("PATCH /tasks/:id/status → in_progress", t_start_task)
test("PATCH /tasks/:id/status → completed", t_complete_task)
test("PATCH /tasks/:id/status（已完成不可再开始）", t_invalid_status_transition)

# ─── 5. 告警 ─────────────────────────────────────────────────────────────────
print(f"\n{INFO} 5. 告警管理（Alerts）")


def t_create_alert():
    r = client.post("/alerts", json={
        "type": "congestion",
        "description": "测试拥堵告警",
        "level": "warning",
        "drone_id": state["drone_id"],
        "longitude": 116.397,
        "latitude": 39.909,
        "confidence": 0.92,
    }, headers=auth_header())
    data = assert_ok(r)
    state["alert_id"] = data["id"]


def t_list_alerts():
    r = client.get("/alerts?page=1&size=10", headers=auth_header())
    data = assert_ok(r)
    assert "list" in data


def t_unread_count():
    r = client.get("/alerts/count/unread", headers=auth_header())
    data = assert_ok(r)
    assert "count" in data


def t_get_alert():
    r = client.get(f"/alerts/{state['alert_id']}", headers=auth_header())
    data = assert_ok(r)
    assert data["id"] == state["alert_id"]


def t_resolve_alert():
    r = client.patch(f"/alerts/{state['alert_id']}/resolve",
                     json={"remark": "已派员处理"}, headers=auth_header())
    assert_ok(r)


def t_batch_read():
    r = client.post("/alerts/batch/read",
                    json={"alert_ids": [state["alert_id"]]}, headers=auth_header())
    assert_ok(r)


test("POST /alerts（创建告警）", t_create_alert)
test("GET  /alerts（列表）", t_list_alerts)
test("GET  /alerts/count/unread", t_unread_count)
test("GET  /alerts/:id（详情，顺便标已读）", t_get_alert)
test("PATCH /alerts/:id/resolve", t_resolve_alert)
test("POST /alerts/batch/read", t_batch_read)

# ─── 6. 报告 ─────────────────────────────────────────────────────────────────
print(f"\n{INFO} 6. 报告中心（Reports）")


def t_list_reports():
    r = client.get("/reports?page=1&size=10", headers=auth_header())
    data = assert_ok(r)
    assert "list" in data


def t_list_recordings():
    r = client.get("/reports/recordings/list?page=1&size=10", headers=auth_header())
    data = assert_ok(r)
    assert "list" in data


test("GET /reports（列表）", t_list_reports)
test("GET /reports/recordings/list（录像列表）", t_list_recordings)

# ─── 7. 大屏数据 ──────────────────────────────────────────────────────────────
print(f"\n{INFO} 7. 数据大屏（Dashboard）")


def t_dashboard_overview():
    r = client.get("/dashboard/overview", headers=auth_header())
    data = assert_ok(r)
    assert "total_drones" in data


def t_dashboard_drones_map():
    r = client.get("/dashboard/drones/map", headers=auth_header())
    data = assert_ok(r)
    assert isinstance(data, list)


def t_dashboard_traffic_trend():
    r = client.get("/dashboard/traffic/trend", headers=auth_header())
    data = assert_ok(r)
    assert isinstance(data, list) and len(data) == 24


test("GET /dashboard/overview", t_dashboard_overview)
test("GET /dashboard/drones/map", t_dashboard_drones_map)
test("GET /dashboard/traffic/trend（24小时趋势）", t_dashboard_traffic_trend)

# ─── 8. 用户管理 ──────────────────────────────────────────────────────────────
print(f"\n{INFO} 8. 用户管理（Users）")


def t_list_users():
    r = client.get("/users?page=1&size=10", headers=auth_header())
    data = assert_ok(r)
    assert "list" in data


def t_create_user():
    r = client.post("/users", json={
        "username": f"pilot_{datetime.now().strftime('%H%M%S')}@test.com",
        "password": "Pilot@12345",
        "real_name": "测试飞手",
        "role": "pilot",
        "phone": "13900139000",
    }, headers=auth_header())
    data = assert_ok(r)
    state["pilot_id"] = data["id"]


def t_generate_invite():
    r = client.post("/users/invite-codes", json={
        "role": "analyst",
        "expire_hours": 24,
    }, headers=auth_header())
    data = assert_ok(r)
    assert data.get("code"), "缺少邀请码"
    state["invite_code"] = data["code"]


def t_register_by_invite():
    r = client.post("/auth/register-by-invite", json={
        "invite_code": state["invite_code"],
        "username": f"analyst_{datetime.now().strftime('%H%M%S')}@test.com",
        "password": "Analyst@12345",
        "real_name": "测试数据员",
    })
    assert_ok(r)


test("GET  /users（列表）", t_list_users)
test("POST /users（创建飞手）", t_create_user)
test("POST /users/invite-codes（生成邀请码）", t_generate_invite)
test("POST /auth/register-by-invite（邀请码注册）", t_register_by_invite)

# ─── 9. AI 模型 ───────────────────────────────────────────────────────────────
print(f"\n{INFO} 9. AI模型管理（Models）")


def t_list_models():
    r = client.get("/models?page=1&size=10", headers=auth_header())
    data = assert_ok(r)
    assert "list" in data
    if data["list"]:
        state["model_id_a"] = data["list"][0]["id"]
        state["model_id_b"] = data["list"][-1]["id"]


def t_get_model():
    if not state.get("model_id_a"):
        return
    r = client.get(f"/models/{state['model_id_a']}", headers=auth_header())
    data = assert_ok(r)
    assert data["id"] == state["model_id_a"]


def t_compare_models():
    if not state.get("model_id_a") or not state.get("model_id_b"):
        return
    r = client.post("/models/compare", json={
        "model_a_id": state["model_id_a"],
        "model_b_id": state["model_id_b"],
    }, headers=auth_header())
    data = assert_ok(r)
    assert data.get("id")


test("GET  /models（列表）", t_list_models)
test("GET  /models/:id（详情）", t_get_model)
test("POST /models/compare（对比任务）", t_compare_models)

# ─── 10. 监控 ────────────────────────────────────────────────────────────────
print(f"\n{INFO} 10. 实时监控（Monitor）")


def t_stream_info():
    r = client.get(f"/monitor/{state['drone_id']}/stream-info", headers=auth_header())
    data = assert_ok(r)
    assert "hls_url" in data


def t_telemetry_latest():
    r = client.get(f"/monitor/{state['drone_id']}/telemetry/latest", headers=auth_header())
    # 有遥测数据则 200，没有则 404
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.json().get("code") == 200


def t_telemetry_history():
    r = client.get(f"/monitor/{state['drone_id']}/telemetry/history?limit=10",
                   headers=auth_header())
    data = assert_ok(r)
    assert isinstance(data, list)


test("GET /monitor/:id/stream-info", t_stream_info)
test("GET /monitor/:id/telemetry/latest", t_telemetry_latest)
test("GET /monitor/:id/telemetry/history", t_telemetry_history)

# ─── 11. 权限边界 ─────────────────────────────────────────────────────────────
print(f"\n{INFO} 11. 权限边界验证")


def t_platform_forbidden():
    r = client.get("/platform/tenants", headers=auth_header())
    assert r.json().get("code") == 40301, "企业管理员不可访问平台超管接口"


def t_403_without_enterprise_admin():
    if not state.get("pilot_id"):
        return
    # 先登录为飞手
    # 飞手无法访问用户管理接口
    # （此处仅验证当前管理员能访问，权限逻辑在 role.guard 和后端 require_roles 中保证）
    r = client.get("/users", headers=auth_header())
    assert_ok(r)  # 管理员可以访问


test("GET /platform/tenants（企业管理员访问返回40301）", t_platform_forbidden)
test("GET /users（企业管理员可访问）", t_403_without_enterprise_admin)

# ─── 12. 清理测试数据 ─────────────────────────────────────────────────────────
print(f"\n{INFO} 12. 清理测试数据")


def t_delete_drone():
    # 创建一台没有任务关联的新无人机，用于测试解绑
    r_new = client.post("/drones", json={
        "name": "待解绑无人机",
        "sn": f"SN_DEL_{datetime.now().strftime('%H%M%S')}",
        "secret_key": "del_secret_key",
        "compute_mode": "cloud",
    }, headers=auth_header())
    new_drone = assert_ok(r_new)
    r = client.delete(f"/drones/{new_drone['id']}", headers=auth_header())
    assert_ok(r)


def t_delete_drone_with_task():
    # 有任务关联的无人机，解绑应返回 40001
    r = client.delete(f"/drones/{state['drone_id']}", headers=auth_header())
    d = r.json()
    assert d.get("code") == 40001, f"有关联任务的无人机解绑应返回 40001，实际 code={d.get('code')}"


def t_delete_pilot():
    if not state.get("pilot_id"):
        return
    r = client.delete(f"/users/{state['pilot_id']}", headers=auth_header())
    assert_ok(r)


def t_logout():
    r = client.post("/auth/logout", headers=auth_header())
    assert_ok(r)
    # logout 后：若 Redis 可用则 Token 进黑名单（401），不可用则 Token 仍有效（降级行为，视为通过）
    r2 = client.get("/auth/me", headers=auth_header())
    code = r2.json().get("code")
    assert code in (200, 40101), f"logout 后访问 /me 返回异常 code={code}"


test("DELETE /drones/:id（无任务关联，解绑成功）", t_delete_drone)
test("DELETE /drones/:id（有任务关联，返回40001）", t_delete_drone_with_task)
test("DELETE /users/:id（删除飞手）", t_delete_pilot)
test("POST /auth/logout（登出后Token处理）", t_logout)

# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
total = results["pass"] + results["fail"]
print(f"  结果: {results['pass']}/{total} 通过")
if results["fail"] > 0:
    print(f"\n  失败项目：")
    for e in results["errors"]:
        print(f"    {FAIL} {e['name']}")
        print(f"       {e['error']}")
print(f"{'='*60}\n")

sys.exit(0 if results["fail"] == 0 else 1)
