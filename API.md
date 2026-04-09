# 接口文档

## 基础信息

- **Base URL**: `http://192.168.66.198:8001`
- **Content-Type**: `application/json`
- **认证方式**: `Authorization: Bearer <access_token>`（部分接口需要）

## 状态码说明

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未授权（Token 无效/过期） |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

## 统一错误响应

```json
{
  "detail": "错误描述"
}
```

## 接口列表

| 方法 | 路径 | 说明 | 需认证 |
|------|------|------|--------|
| POST | `/users` | 创建用户 | ❌ |
| GET | `/users` | 获取用户列表 | ❌ |
| GET | `/users/{id}` | 获取单个用户 | ❌ |
| PUT | `/users/{id}` | 更新用户 | ❌ |
| DELETE | `/users/{id}` | 删除用户 | ❌ |
| POST | `/users/login` | 登录 | ❌ |
| POST | `/users/token/refresh` | 刷新 Token | ❌ |
| POST | `/users/token/revoke` | 撤销 Token | ✅ |
| GET | `/users/token/check` | 验证 Token | ❌ |
| POST | `/users/token/get` | 获取 Token | ❌ |

---

## 1. 创建用户

**请求**：
```bash
POST /users
Content-Type: application/json

{
  "username": "zhangsan",
  "password": "123456",
  "phone": "13800138000",
  "email": "zhangsan@example.com"  // 可选
}
```

**逻辑**：
1. 接收用户名、密码、手机号
2. 用 Argon2 把密码加密
3. 自动生成 uid（32位随机字符串）
4. 写入数据库
5. 返回用户信息（不含密码）

**返回示例**：
```json
{
  "id": 1,
  "uid": "a1b2c3d4e5f6...",
  "username": "zhangsan",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "created_at": "2026-04-07T10:00:00",
  "updated_at": "2026-04-07T10:00:00"
}
```

---

## 2. 登录

**请求**：
```bash
POST /users/login
Content-Type: application/json

{
  "username": "zhangsan",
  "password": "123456"
}
```

**逻辑**：
1. 根据用户名查数据库
2. 用 Argon2 验证密码
3. 生成 access_token（1小时）+ refresh_token（7天）
4. refresh_token 存入数据库
5. 返回两个 Token + 用户信息

**返回示例**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "uid": "a1b2c3d4...",
    "username": "zhangsan",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "created_at": "2026-04-07T10:00:00",
    "updated_at": "2026-04-07T10:00:00"
  }
}
```

---

## 3. 刷新 Token

**请求**：
```bash
POST /users/token/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**逻辑**：
1. 验证 refresh_token 格式和签名
2. 检查数据库中是否存在（是否被撤销）
3. 检查是否过期
4. 删除旧的 refresh_token
5. 生成新的 access_token + refresh_token
6. 保存新的 refresh_token

**返回示例**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 4. 撤销 Token（退出登录）

**请求**：
```bash
POST /users/token/revoke
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

**逻辑**：
1. 验证 access_token
2. 删除该用户的所有 refresh_token（强制所有设备下线）

**返回示例**：
```json
{
  "message": "已撤销所有Token，请重新登录"
}
```

---

## 5. 验证 Token

**请求**：
```bash
GET /users/token/check
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

**说明**：验证 access_token 是否有效

**返回示例**：
```json
// Token 有效
{
  "valid": true,
  "user_id": 1,
  "username": "zhangsan",
  "message": "Token有效"
}

// Token 无效或过期
{
  "valid": false,
  "message": "Token无效或已过期"
}
```

---

## 6. 获取 Token（兼容旧接口）

**请求**：
```bash
POST /users/token/get
Content-Type: application/json

{
  "username": "zhangsan",
  "password": "123456"
}
```

**说明**：兼容旧接口，功能同 `/login`

**返回示例**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 7. 获取用户列表

**请求**：
```bash
GET /users?page=1&page_size=20
```

**参数**：
- `page`：页码，默认 1
- `page_size`：每页数量，默认 20

**返回示例**：
```json
[
  {
    "id": 1,
    "uid": "a1b2c3d4...",
    "username": "zhangsan",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "created_at": "2026-04-07T10:00:00",
    "updated_at": "2026-04-07T10:00:00"
  }
]
```

---

## 8. 获取单个用户

**请求**：
```bash
GET /users/1
```

**返回示例**：
```json
{
  "id": 1,
  "uid": "a1b2c3d4...",
  "username": "zhangsan",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "created_at": "2026-04-07T10:00:00",
  "updated_at": "2026-04-07T10:00:00"
}
```

---

## 9. 更新用户

**请求**：
```bash
PUT /users/1
Content-Type: application/json

{
  "phone": "13900139000",
  "email": "new@example.com"
}
```

**说明**：
- 只更新提供的字段
- 如果提供 `password` 字段，会自动重新加密

**返回示例**：
```json
{
  "id": 1,
  "uid": "a1b2c3d4...",
  "username": "zhangsan",
  "phone": "13900139000",
  "email": "new@example.com",
  "created_at": "2026-04-07T10:00:00",
  "updated_at": "2026-04-07T12:00:00"
}
```

---

## 10. 删除用户

**请求**：
```bash
DELETE /users/1
```

**返回示例**：
```json
{
  "message": "删除成功"
}
```

---

## Token 说明

### 两种 Token

| Token 类型 | 有效期 | 用途 |
|-----------|--------|------|
| Access Token | 1 小时 | 访问接口 |
| Refresh Token | 7 天 | 刷新 Access Token |

### 工作流程

```
1. 登录 → 返回 access_token + refresh_token
       ↓
2. 访问接口 → Header: Authorization: Bearer <access_token>
       ↓
3. access_token 过期 → 前端收到 401
       ↓
4. 用 refresh_token 换新的 tokens → POST /users/token/refresh
       ↓
5. 继续访问，直到 refresh_token 也过期
       ↓
6. refresh_token 过期 → 重新登录
```

### 存储建议

- **access_token**：放在内存中（不持久化），每次请求用
- **refresh_token**：存 localStorage 或 httpOnly cookie
- 请求时 Header：`Authorization: Bearer <access_token>`

### 强制下线

调用 `POST /users/token/revoke` 会删除该用户的所有 refresh_token，所有设备都需要重新登录。

---

## 典型前端逻辑

```javascript
// 登录
const login = async (username, password) => {
  const res = await fetch('/users/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  localStorage.setItem('refresh_token', data.refresh_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data.access_token;
};

// 请求封装
const request = async (url, options = {}) => {
  let accessToken = localStorage.getItem('access_token');
  
  options.headers = options.headers || {};
  options.headers['Authorization'] = `Bearer ${accessToken}`;
  
  let res = await fetch(url, options);
  
  if (res.status === 401) {
    // access_token 过期，刷新
    const refreshToken = localStorage.getItem('refresh_token');
    const refreshRes = await fetch('/users/token/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      
      // 重试原请求
      options.headers['Authorization'] = `Bearer ${data.access_token}`;
      res = await fetch(url, options);
    } else {
      // refresh_token 也失效，重新登录
      // window.location.href = '/login';
    }
  }
  
  return res;
};
```
