import os
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nas_demo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("NAS_DEMO_SECRET", "nas-demo-secret")

db = SQLAlchemy(app)


FUNCTIONAL_OVERVIEW = {
    "background": {
        "title": "项目背景",
        "points": [
            "素材散落在移动硬盘/个人网盘，备份与检索体验差",
            "硬盘损坏风险高、网盘限速导致传输耗时",
            "多人协作权限混乱，版本不可控",
        ],
    },
    "goals": {
        "title": "业务目标",
        "highlights": [
            "降低素材丢失风险 (RAID + 云端备份)",
            "提升日常剪辑与检索效率",
            "减少手工传盘/上传，配合自动同步策略",
            "提供基础的多人协作与权限管理",
        ],
    },
    "modules": [
        {
            "name": "本地存储与 RAID 管理",
            "description": "统一纳管物理磁盘、阵列、容量快照",
            "features": [
                "磁盘识别、温度与 S.M.A.R.T 健康监测",
                "RAID1/5/10 创建、状态展示、重建提示",
                "卷/共享空间容量监控，支持快照 (选配)",
            ],
        },
        {
            "name": "项目 / 文件管理",
            "description": "把素材组织成项目结构并提供导入向导",
            "features": [
                "项目模板、状态、客户信息、目录初始化",
                "文件浏览、上传/导入、移动/删除操作",
                "U 盘/读卡器导入向导与重复检测",
            ],
        },
        {
            "name": "标签与元数据",
            "description": "采集媒体信息并支撑业务字段",
            "features": [
                "自动记录分辨率、帧率、拍摄时间等技术元数据",
                "客户、拍摄日期、摄影师、机位、场景等自定义字段",
                "单个/批量编辑与多标签打标",
            ],
        },
        {
            "name": "检索与预览",
            "description": "快速定位素材并查看缩略图/详情",
            "features": [
                "关键字全局搜索 (项目/客户/标签/文件名)",
                "按项目、时间、类型、分辨率、标签筛选",
                "列表/缩略图视图与常用视图收藏",
            ],
        },
        {
            "name": "云存储与网盘接入",
            "description": "统一配置对象存储与网盘账号",
            "features": [
                "多对象存储目标 (Endpoint、AK/SK、路径前缀)",
                "WebDAV、官方 API、扫码授权等接入模式",
                "存储目标启停、编辑、连接测试",
            ],
        },
        {
            "name": "同步与分层存储",
            "description": "智能调度本地/云端同步并控制热温冷策略",
            "features": [
                "源路径、方向、过滤器、冲突策略的同步任务定义",
                "定时/窗口/限速调度、断点续传与差异对比",
                "Hot/Warm/Cold 策略、冷数据本地缓存与回迁流程",
            ],
        },
        {
            "name": "用户、角色与权限",
            "description": "保障协作安全与项目隔离",
            "features": [
                "用户生命周期管理与密码重置",
                "预置角色 (管理员/负责人/成员) 绑定权限",
                "项目维度的浏览/上传/删除/管理授权",
            ],
        },
        {
            "name": "运维监控与告警",
            "description": "确保设备状态透明并及时预警",
            "features": [
                "磁盘健康、阵列状态、温度/S.M.A.R.T 展示",
                "容量阈值告警、任务失败日志、邮件通知",
                "扩容/迁移向导，网络与云连通性自检",
            ],
        },
        {
            "name": "系统与配置管理",
            "description": "提供网络、协议、备份等系统级设置",
            "features": [
                "主机名、时区、语言、管理员密码等基础设置",
                "IP/网关/DNS/SMB/NFS 等网络共享管理",
                "系统配置/元数据库备份与恢复",
            ],
        },
        {
            "name": "Web 界面",
            "description": "面向用户与管理员的操作入口",
            "features": [
                "素材浏览、搜索、导入、冷数据恢复",
                "存储配置、同步任务、告警总览",
                "多角色自适应的仪表盘",
            ],
        },
    ],
}


PRD_DATA = {
    "product": {
        "name": "创作 NAS 混合云存储系统（V1）",
        "purpose": "为个人摄像师、小型工作室、中小制作团队提供“本地 NAS + 云端存储 + 智能同步”的一体化平台，取代零散硬盘与限速网盘。",
        "goals": [
            "80% 素材纳入统一 NAS 管理，减少移动硬盘依赖",
            "新项目建档 + 素材导入 + 云备份 30 分钟内完成",
            "热/温/冷策略让本地冷数据占用降低 30%",
            "支撑 5–10 人协作，权限明确可控",
        ],
    },
    "owners": [
        {
            "role": "老板 / 制片人",
            "focus": ["数据安全可追溯", "总体成本可控", "流程一键可视"],
        },
        {
            "role": "技术 / 设备负责人",
            "focus": ["扩容简单", "备份可靠", "告警可落地"],
        },
        {
            "role": "摄像师 / 剪辑师",
            "focus": ["导入快", "访问快", "检索快"],
        },
    ],
    "scenarios": [
        "拍摄归来快速导入并生成目录",
        "NAS 作为统一素材盘支撑多机剪辑",
        "项目完成一键归档到云端对象存储/网盘",
        "历史项目按标签/客户检索并回迁冷数据",
        "多人项目的权限隔离和审批",
        "磁盘健康、容量、扩容指引的日常运维",
    ],
    "scope": {
        "must": [
            "RAID/卷管理与状态监控",
            "项目/文件/目录与导入能力",
            "标签、元数据管理与检索预览",
            "对象存储、网盘接入与同步任务",
            "热/温/冷分层策略和冷数据清理",
            "RBAC 角色与项目级权限",
            "磁盘/容量告警与运维面板",
            "Creator/管理端 Web UI",
        ],
        "exclude": [
            "完整 MAM 工作流、审片与版本树",
            "AI 内容识别与语义检索",
            "复杂多租户（单台设备服务多个组织）",
        ],
    },
    "processes": [
        {
            "name": "项目生命周期",
            "steps": [
                "创建项目并填写客户、负责人、云端策略",
                "导入素材生成目录树并持续写入",
                "项目完成后触发云归档任务",
                "按策略降温并释放冷数据",
            ],
        },
        {
            "name": "导入流程",
            "steps": [
                "检测外部设备并发起导入向导",
                "映射到项目目录并可选重命名规则",
                "执行复制与重试，完成后解析元数据",
            ],
        },
        {
            "name": "云同步",
            "steps": [
                "配置对象存储或网盘",
                "定义同步任务（源/目标/策略/限速）",
                "调度器执行差异比对、分片上传、记录日志",
            ],
        },
        {
            "name": "冷数据恢复",
            "steps": [
                "用户点击 cloud-only 文件",
                "系统提示恢复并生成任务",
                "从云端下载、回写 NAS 并更新索引",
            ],
        },
    ],
    "modules": [
        {
            "name": "内容管理域",
            "capabilities": ["项目管理", "文件/目录操作", "标签与元数据", "检索与预览"],
        },
        {
            "name": "存储与同步域",
            "capabilities": ["本地存储/RAID", "云接入", "同步任务", "分层策略"],
        },
        {
            "name": "安全与账户域",
            "capabilities": ["用户/角色", "项目级权限", "操作审计"],
        },
        {
            "name": "运维与系统域",
            "capabilities": ["监控与告警", "扩容向导", "配置备份"],
        },
    ],
    "metrics": [
        {"name": "导入效率", "target": "单个项目建档 + 导入 + 备份 ≤ 30 分钟"},
        {"name": "容量释放", "target": "冷数据本地占用下降 ≥ 30%"},
        {"name": "协作体验", "target": "5–10 人并发访问无明显卡顿"},
        {"name": "安全性", "target": "核心操作 100% 有审计记录"},
    ],
}


DESIGN_DATA = {
    "components": {
        "frontend": [
            {"name": "Web 用户端", "desc": "供 Creator 浏览项目、导入、检索、发起冷数据恢复"},
            {"name": "Web 管理端", "desc": "供管理员配置存储、同步、策略、用户与告警"},
        ],
        "services": [
            "Auth & RBAC：认证、Token、权限校验",
            "Project & Asset：项目、目录、导入任务管理",
            "Metadata & Search：元数据与检索索引",
            "Sync & Tiering：同步任务、分层策略调度",
            "Cloud Adapter：S3/OSS/COS/WebDAV/网盘驱动",
            "Storage & Health：磁盘、RAID、S.M.A.R.T 采集",
            "Monitoring & Alert：指标、告警与通知",
            "Audit Log：行为日志归档",
        ],
        "storage": [
            "NAS 卷（POSIX 文件系统）",
            "关系型数据库（项目/资产/策略/用户）",
            "搜索引擎或 DB 索引（标签、检索）",
        ],
    },
    "data_models": [
        {
            "name": "Project",
            "fields": [
                ("name", "项目名称"),
                ("client_name", "客户"),
                ("owner_user_id", "负责人"),
                ("status", "ongoing/completed/archived"),
                ("default_storage_target_id", "默认云目标"),
                ("tier_policy_id", "绑定的分层策略"),
            ],
        },
        {
            "name": "Asset",
            "fields": [
                ("project_id", "所属项目"),
                ("parent_folder_id", "父目录"),
                ("file_name", "文件名"),
                ("file_path", "NAS 路径"),
                ("size", "大小"),
                ("type", "video/image/audio/other"),
                ("media_meta", "分辨率/时长/帧率"),
                ("shoot_date", "拍摄日期"),
                ("local_presence", "local_only/local+cloud/cloud_only"),
                ("tier_level", "hot/warm/cold"),
            ],
        },
        {
            "name": "StorageTarget",
            "fields": [
                ("type", "对象存储或网盘"),
                ("provider", "OSS/COS/S3/XXX 网盘"),
                ("config", "endpoint/bucket/token"),
                ("status", "active/inactive"),
            ],
        },
        {
            "name": "SyncTask",
            "fields": [
                ("source_type", "project/folder"),
                ("source_ids", "支持多项目/目录"),
                ("target_ids", "可多目标"),
                ("direction", "local_to_cloud/cloud_to_local/bidirectional"),
                ("mode", "full/incremental"),
                ("filter_rules", "类型/大小/前缀"),
                ("schedule_expr", "cron 或窗口"),
                ("bandwidth_limit", "上下行限速"),
            ],
        },
        {
            "name": "TierPolicy",
            "fields": [
                ("hot_to_warm_days", "转温阈值"),
                ("warm_to_cold_days", "转冷阈值"),
                ("cold_local_cache_limit", "冷数据本地缓存上限"),
            ],
        },
        {
            "name": "User/Role/Permission",
            "fields": [
                ("User", "username/password_hash/email/status"),
                ("Role", "角色 + 描述"),
                ("RolePermission", "角色授权的菜单/操作"),
                ("ProjectMember", "项目维度 owner/editor/viewer"),
            ],
        },
    ],
    "apis": [
        {
            "category": "认证与用户",
            "endpoints": [
                {"method": "POST", "path": "/api/auth/login", "desc": "用户名+密码换取 Token"},
                {"method": "GET", "path": "/api/users", "desc": "用户列表"},
                {"method": "POST", "path": "/api/users", "desc": "创建用户"},
                {"method": "PATCH", "path": "/api/users/{id}/disable", "desc": "禁用/启用"},
            ],
        },
        {
            "category": "项目与素材",
            "endpoints": [
                {"method": "GET", "path": "/api/projects", "desc": "条件检索项目"},
                {"method": "POST", "path": "/api/projects", "desc": "新建项目"},
                {"method": "PATCH", "path": "/api/projects/{id}", "desc": "更新项目状态/信息"},
                {"method": "GET", "path": "/api/projects/{id}/tree", "desc": "目录树"},
                {"method": "POST", "path": "/api/assets/import", "desc": "导入任务入口"},
                {"method": "POST", "path": "/api/assets/search", "desc": "组合检索"},
            ],
        },
        {
            "category": "云存储与同步",
            "endpoints": [
                {"method": "POST", "path": "/api/storage-targets", "desc": "新增对象存储目标"},
                {"method": "POST", "path": "/api/netdisk/{provider}/bind", "desc": "扫码/授权"},
                {"method": "GET", "path": "/api/sync-tasks", "desc": "任务列表"},
                {"method": "POST", "path": "/api/sync-tasks", "desc": "创建任务"},
                {"method": "POST", "path": "/api/sync-tasks/{id}/run", "desc": "手动执行"},
            ],
        },
        {
            "category": "策略与运维",
            "endpoints": [
                {"method": "GET", "path": "/api/tier-policies", "desc": "策略列表"},
                {"method": "PATCH", "path": "/api/projects/{id}/tier-policy", "desc": "绑定策略"},
                {"method": "GET", "path": "/api/dashboard/overview", "desc": "容量、健康、任务"},
                {"method": "GET", "path": "/api/alerts", "desc": "告警列表"},
            ],
        },
    ],
    "flows": [
        {
            "title": "导入任务",
            "steps": [
                "前端发起 /api/assets/import，记录导入任务",
                "Worker 扫描来源并复制到 NAS",
                "每完成一个文件即写入 Asset 表并异步解析媒体信息",
                "前端轮询任务状态并刷新目录",
            ],
        },
        {
            "title": "同步任务调度",
            "steps": [
                "调度器按 cron 拉取到期 SyncTask",
                "差异比对生成文件列表并拆分子 Job",
                "调用 Cloud Adapter 分片上传并记录日志",
                "更新 SyncRecord、Asset.local_presence 并处理失败重试",
            ],
        },
        {
            "title": "分层迁移",
            "steps": [
                "定时扫描 Asset.last_accessed 与策略阈值",
                "热→温/温→冷时更新 tier_level 与 local_presence",
                "需要释放冷数据时生成删除任务并仅保留索引、缩略图",
                "用户访问 cloud-only 文件会触发恢复任务，从云端拉回",
            ],
        },
        {
            "title": "权限校验",
            "steps": [
                "前端携带 Token 调用 API",
                "Auth 服务解析 user_id 并校验有效期",
                "结合 ProjectMember/RolePermission 判断是否可操作",
                "审计日志记录动作与结果",
            ],
        },
    ],
    "security": [
        "采用 HTTPS + JWT/Session Token，密码加盐哈希存储",
        "云端 AK/SK、网盘 Token 加密存放，访问时临时解密",
        "Cloud Adapter 按驱动扩展，新增 provider 无需改核心逻辑",
        "导入/同步任务可横向扩展 Worker，避免阻塞主线程",
        "关键操作写入 AuditLog 并可导出以满足合规",
    ],
}


# Association tables
file_tags = db.Table(
    "file_tags",
    db.Column("file_id", db.Integer, db.ForeignKey("file_asset.id")),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
)

project_members = db.Table(
    "project_members",
    db.Column("project_id", db.Integer, db.ForeignKey("project.id")),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
)

sync_task_targets = db.Table(
    "sync_task_targets",
    db.Column("sync_task_id", db.Integer, db.ForeignKey("sync_task.id")),
    db.Column("storage_target_id", db.Integer, db.ForeignKey("storage_target.id")),
)


class RaidArray(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(30), default="Healthy")
    capacity_total = db.Column(db.Integer)
    capacity_used = db.Column(db.Integer)
    notes = db.Column(db.Text)
    disks = db.relationship("Disk", backref="raid", lazy=True)


class Disk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.String(50), nullable=False)
    capacity_gb = db.Column(db.Integer, nullable=False)
    temperature = db.Column(db.Float, default=35.0)
    smart_status = db.Column(db.String(30), default="OK")
    health = db.Column(db.String(30), default="Healthy")
    raid_id = db.Column(db.Integer, db.ForeignKey("raid_array.id"))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default="进行中")
    project_state = db.Column(db.String(30), default="Hot")
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    last_accessed = db.Column(db.DateTime)
    location = db.Column(db.String(100))
    policy = db.relationship("StoragePolicy", backref="project", uselist=False)
    files = db.relationship("FileAsset", backref="project", lazy=True)


class FileAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    folder = db.Column(db.String(120))
    name = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(20))
    size_mb = db.Column(db.Integer)
    resolution = db.Column(db.String(20))
    duration_seconds = db.Column(db.Integer)
    frame_rate = db.Column(db.String(10))
    codec = db.Column(db.String(50))
    camera = db.Column(db.String(100))
    location = db.Column(db.String(100))
    storage_state = db.Column(db.String(20), default="Hot")
    local_available = db.Column(db.Boolean, default=True)
    cloud_synced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    tags = db.relationship("Tag", secondary=file_tags, backref="files")


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class StorageTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    endpoint = db.Column(db.String(200))
    bucket = db.Column(db.String(100))
    access_key = db.Column(db.String(100))
    description = db.Column(db.Text)
    auth_mode = db.Column(db.String(50))
    extra = db.Column(db.Text)


class SyncTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    project = db.relationship("Project", backref="sync_tasks")
    source_path = db.Column(db.String(200))
    direction = db.Column(db.String(20), default="NAS→云端")
    mode = db.Column(db.String(20), default="增量")
    schedule = db.Column(db.String(50))
    bandwidth_high = db.Column(db.Integer)
    bandwidth_low = db.Column(db.Integer)
    status = db.Column(db.String(30), default="未启动")
    conflict_strategy = db.Column(db.String(30), default="以本地为准")
    file_filter = db.Column(db.String(120))
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    targets = db.relationship("StorageTarget", secondary=sync_task_targets, backref="tasks")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(50), default="普通成员")
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    projects = db.relationship("Project", secondary=project_members, backref="members")


class StoragePolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    hot_to_warm_days = db.Column(db.Integer, default=7)
    warm_to_cold_months = db.Column(db.Integer, default=3)
    keep_local_hot = db.Column(db.Boolean, default=True)
    keep_local_warm = db.Column(db.Boolean, default=True)
    keep_local_cold = db.Column(db.Boolean, default=False)


class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))
    action = db.Column(db.String(100))
    detail = db.Column(db.Text)
    username = db.Column(db.String(80))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def log_event(category: str, action: str, detail: str, username: str = "system"):
    entry = LogEntry(category=category, action=action, detail=detail, username=username)
    db.session.add(entry)
    db.session.commit()


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


def seed_data():
    if User.query.first():
        return

    admin = User(username="admin", role="系统管理员", email="admin@example.com", phone="13800138000")
    lead = User(username="director", role="项目负责人", email="lead@example.com")
    member = User(username="editor", role="普通成员", email="editor@example.com")

    db.session.add_all([admin, lead, member])

    raid = RaidArray(name="影片阵列", level="RAID5", status="Healthy", capacity_total=32000, capacity_used=12000)
    disks = [
        Disk(serial=f"Disk-{i}", capacity_gb=8000, temperature=32 + i, smart_status="OK", raid=raid)
        for i in range(1, 5)
    ]
    db.session.add(raid)
    db.session.add_all(disks)

    proj1 = Project(
        name="品牌宣传片",
        client_name="星河科技",
        description="新品发布宣传片",
        status="进行中",
        project_state="Hot",
        start_date=datetime.utcnow().date() - timedelta(days=3),
        last_accessed=datetime.utcnow(),
        location="上海",
    )
    proj2 = Project(
        name="纪录片《远行》",
        client_name="纪实频道",
        description="六集纪录片后期",
        status="已完成",
        project_state="Warm",
        start_date=datetime.utcnow().date() - timedelta(days=50),
        last_accessed=datetime.utcnow() - timedelta(days=12),
        location="北京",
    )

    db.session.add_all([proj1, proj2])
    proj1.members.extend([admin, lead, member])
    proj2.members.extend([lead, member])

    policy1 = StoragePolicy(project=proj1, hot_to_warm_days=10, warm_to_cold_months=4)
    policy2 = StoragePolicy(project=proj2, hot_to_warm_days=7, warm_to_cold_months=2, keep_local_cold=False)
    db.session.add_all([policy1, policy2])

    tag_city = Tag(name="城市夜景")
    tag_drone = Tag(name="航拍")
    tag_client = Tag(name="客户访谈")
    db.session.add_all([tag_city, tag_drone, tag_client])

    file1 = FileAsset(
        project=proj1,
        folder="原始素材",
        name="A001_C001_010101.mov",
        file_type="视频",
        size_mb=20480,
        resolution="4K",
        duration_seconds=45,
        frame_rate="25",
        codec="ProRes",
        camera="FX6",
        location="上海陆家嘴",
        storage_state="Hot",
        cloud_synced=True,
        notes="夜景无人机镜头",
    )
    file1.tags.extend([tag_city, tag_drone])

    file2 = FileAsset(
        project=proj1,
        folder="工程文件",
        name="Promo_edit_v1.prproj",
        file_type="工程",
        size_mb=1500,
        storage_state="Hot",
        cloud_synced=False,
    )

    file3 = FileAsset(
        project=proj2,
        folder="输出成片",
        name="Episode1_master.mp4",
        file_type="视频",
        size_mb=4096,
        resolution="4K",
        duration_seconds=1200,
        frame_rate="25",
        codec="H.265",
        storage_state="Warm",
        cloud_synced=True,
    )
    file3.tags.append(tag_client)

    db.session.add_all([file1, file2, file3])

    s3 = StorageTarget(
        name="华南对象存储",
        target_type="对象存储",
        endpoint="https://oss-cn-shenzhen.aliyuncs.com",
        bucket="studio-archive",
        access_key="AKIA***",
        auth_mode="AK/SK",
        description="用于长期归档",
    )
    webdav = StorageTarget(
        name="团队网盘",
        target_type="网盘(WebDAV)",
        endpoint="https://dav.example.com",
        bucket="/studio",
        auth_mode="账号密码",
        description="成员日常共享",
    )
    db.session.add_all([s3, webdav])

    task = SyncTask(
        name="宣传片云备份",
        project=proj1,
        source_path="/projects/promo",
        direction="NAS→云端",
        mode="增量",
        schedule="每日 02:00",
        bandwidth_high=80,
        bandwidth_low=20,
        status="运行中",
        conflict_strategy="以本地为准",
        last_run=datetime.utcnow() - timedelta(hours=5),
        next_run=datetime.utcnow() + timedelta(hours=19),
        file_filter="*.mov;*.prproj",
    )
    task.targets.extend([s3, webdav])
    db.session.add(task)

    log_entries = [
        LogEntry(category="登录", action="用户登录", detail="admin 登录了系统", username="admin"),
        LogEntry(category="文件", action="上传素材", detail="A001_C001 上传成功", username="director"),
        LogEntry(category="同步", action="任务完成", detail="宣传片云备份完成", username="system"),
    ]
    db.session.add_all(log_entries)

    db.session.commit()


@app.before_request
def ensure_db_seeded():
    db.create_all()
    seed_data()


@app.route("/")
def dashboard():
    projects = Project.query.all()
    files = FileAsset.query.all()
    disks = Disk.query.all()
    tasks = SyncTask.query.all()
    raids = RaidArray.query.all()
    targets = StorageTarget.query.all()
    recent_logs = LogEntry.query.order_by(LogEntry.timestamp.desc()).limit(6).all()

    total_capacity = sum(d.capacity_gb for d in disks)
    used_capacity = sum(r.capacity_used or 0 for r in raids)
    used_percent = (used_capacity / total_capacity * 100) if total_capacity else 0
    hot_files = len([f for f in files if f.storage_state == "Hot"])
    warm_files = len([f for f in files if f.storage_state == "Warm"])
    cold_files = len([f for f in files if f.storage_state == "Cold"])
    tier_labels = ["Hot", "Warm", "Cold"]
    tier_values = [hot_files, warm_files, cold_files]
    tier_colors = ["#22d3ee", "#818cf8", "#f472b6"]
    tier_breakdown = {
        "labels": tier_labels,
        "values": tier_values,
        "colors": tier_colors,
        "pairs": list(zip(tier_labels, tier_values, tier_colors)),
    }

    healthy_disks = len([d for d in disks if (d.health or "").lower().startswith("healthy")])
    unsynced_files = len([f for f in files if not f.cloud_synced])
    running_tasks = len([t for t in tasks if t.status in ("运行中", "同步中")])
    scheduled_tasks = len(tasks) - running_tasks
    active_projects = len([p for p in projects if p.status == "进行中"])
    tag_count = Tag.query.count()
    policy_projects = StoragePolicy.query.count()

    alerts = []
    if used_percent > 85:
        alerts.append(f"阵列容量已使用 {used_percent:.1f}% ，请评估扩容或冷迁策略")
    hot_disks = [disk for disk in disks if disk.temperature and disk.temperature > 50]
    if hot_disks:
        disks_label = "、".join(d.serial for d in hot_disks[:3])
        alerts.append(f"{disks_label} 温度偏高，请检查风道（共 {len(hot_disks)} 块）")
    if unsynced_files:
        alerts.append(f"有 {unsynced_files} 个文件尚未云端同步")

    next_run_times = [task.next_run for task in tasks if task.next_run]
    next_run_str = min(next_run_times).strftime("%m-%d %H:%M") if next_run_times else "未排程"

    target_names = ", ".join(t.name for t in targets[:2])
    if len(targets) > 2:
        target_names += f" 等 {len(targets)} 个"

    service_status = [
        {
            "name": "NAS 控制器",
            "status": "ONLINE",
            "status_level": "success",
            "description": f"{healthy_disks}/{len(disks)} 块磁盘健康 · {len(raids)} 套阵列",
            "kpi": f"容量利用率 {used_percent:.1f}%",
        },
        {
            "name": "同步编排",
            "status": "SCHEDULED" if tasks else "IDLE",
            "status_level": "info" if tasks else "warning",
            "description": f"{len(tasks)} 个任务 / {running_tasks} 正在运行",
            "kpi": f"下一窗口 {next_run_str}",
        },
        {
            "name": "云接入",
            "status": "READY" if targets else "未配置",
            "status_level": "success" if targets else "warning",
            "description": f"{len(targets)} 个对象存储/网盘目标",
            "kpi": target_names or "尚未添加外部目标",
        },
        {
            "name": "资产索引",
            "status": "ACTIVE",
            "status_level": "success",
            "description": f"{len(files)} 个文件 · {tag_count} 个标签",
            "kpi": f"策略覆盖 {policy_projects} 个项目",
        },
    ]

    return render_template(
        "dashboard.html",
        projects=projects,
        files=files,
        disks=disks,
        tasks=tasks,
        total_capacity=total_capacity,
        used_capacity=used_capacity,
        hot_files=hot_files,
        warm_files=warm_files,
        cold_files=cold_files,
        tier_breakdown=tier_breakdown,
        service_status=service_status,
        alerts=alerts,
        recent_logs=recent_logs,
        used_percent=used_percent,
        active_projects=active_projects,
        running_tasks=running_tasks,
        scheduled_tasks=scheduled_tasks,
        unsynced_files=unsynced_files,
        healthy_disks=healthy_disks,
        targets=targets,
    )


@app.route("/projects", methods=["GET", "POST"])
def project_list():
    if request.method == "POST":
        name = request.form.get("name")
        client = request.form.get("client")
        status = request.form.get("status")
        description = request.form.get("description")
        project_state = request.form.get("project_state", "Hot")
        location = request.form.get("location")

        project = Project(
            name=name,
            client_name=client,
            status=status,
            description=description,
            project_state=project_state,
            start_date=datetime.utcnow().date(),
            last_accessed=datetime.utcnow(),
            location=location,
        )
        db.session.add(project)
        db.session.commit()
        log_event("项目", "创建项目", f"创建项目 {name}")
        flash("项目创建成功", "success")
        return redirect(url_for("project_list"))

    keyword = request.args.get("keyword", "").strip()
    status = request.args.get("status")
    tier = request.args.get("tier")

    query = Project.query
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(db.or_(Project.name.ilike(like), Project.client_name.ilike(like)))
    if status:
        query = query.filter_by(status=status)
    if tier:
        query = query.filter_by(project_state=tier)

    projects = query.order_by(Project.last_accessed.desc().nullslast()).all()
    return render_template("projects.html", projects=projects)


@app.route("/projects/<int:project_id>", methods=["GET", "POST"])
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_status":
            project.status = request.form.get("status")
            project.project_state = request.form.get("project_state")
            project.last_accessed = datetime.utcnow()
            db.session.commit()
            log_event("项目", "更新状态", f"项目 {project.name} 更新状态")
            flash("项目状态已更新", "success")
        elif action == "add_member":
            user_id = int(request.form.get("user_id"))
            user = User.query.get(user_id)
            if user and user not in project.members:
                project.members.append(user)
                db.session.commit()
                flash("成员已添加", "success")
        elif action == "update_policy":
            hot_days = int(request.form.get("hot_days"))
            warm_months = int(request.form.get("warm_months"))
            keep_warm = bool(request.form.get("keep_warm"))
            keep_cold = bool(request.form.get("keep_cold"))
            if not project.policy:
                project.policy = StoragePolicy()
            project.policy.hot_to_warm_days = hot_days
            project.policy.warm_to_cold_months = warm_months
            project.policy.keep_local_warm = keep_warm
            project.policy.keep_local_cold = keep_cold
            db.session.commit()
            flash("分层策略已更新", "success")

    files = FileAsset.query.filter_by(project_id=project_id).all()
    users = User.query.all()
    return render_template("project_detail.html", project=project, files=files, users=users)


@app.route("/projects/<int:project_id>/files", methods=["POST"])
def add_file(project_id):
    project = Project.query.get_or_404(project_id)
    file = FileAsset(
        project=project,
        folder=request.form.get("folder"),
        name=request.form.get("name"),
        file_type=request.form.get("file_type"),
        size_mb=int(request.form.get("size_mb", 0) or 0),
        resolution=request.form.get("resolution"),
        duration_seconds=int(request.form.get("duration", 0) or 0),
        frame_rate=request.form.get("frame_rate"),
        codec=request.form.get("codec"),
        camera=request.form.get("camera"),
        location=request.form.get("location"),
        storage_state=request.form.get("storage_state", "Hot"),
        local_available=request.form.get("local_available") == "on",
        cloud_synced=request.form.get("cloud_synced") == "on",
        notes=request.form.get("notes"),
    )
    db.session.add(file)
    db.session.commit()
    log_event("文件", "导入文件", f"{file.name} 导入到 {project.name}")
    flash("文件已导入", "success")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/files/<int:file_id>", methods=["GET", "POST"])
def file_detail(file_id):
    file = FileAsset.query.get_or_404(file_id)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_metadata":
            file.folder = request.form.get("folder")
            file.file_type = request.form.get("file_type")
            file.size_mb = int(request.form.get("size_mb", 0) or 0)
            file.resolution = request.form.get("resolution")
            file.duration_seconds = int(request.form.get("duration", 0) or 0)
            file.frame_rate = request.form.get("frame_rate")
            file.codec = request.form.get("codec")
            file.camera = request.form.get("camera")
            file.location = request.form.get("location")
            file.storage_state = request.form.get("storage_state")
            file.local_available = request.form.get("local_available") == "on"
            file.cloud_synced = request.form.get("cloud_synced") == "on"
            file.notes = request.form.get("notes")
            db.session.commit()
            log_event("文件", "更新元数据", f"更新 {file.name}")
            flash("文件信息已更新", "success")
        elif action == "add_tag":
            tag_name = request.form.get("tag_name")
            if tag_name:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                if tag not in file.tags:
                    file.tags.append(tag)
                    db.session.commit()
        elif action == "remove_tag":
            tag_id = int(request.form.get("tag_id"))
            tag = Tag.query.get(tag_id)
            if tag and tag in file.tags:
                file.tags.remove(tag)
                db.session.commit()
        elif action == "restore":
            file.local_available = True
            log_event("文件", "冷数据恢复", f"触发 {file.name} 恢复")
            db.session.commit()
            flash("已提交云端回迁请求", "info")

    tags = Tag.query.order_by(Tag.name).all()
    return render_template("file_detail.html", file=file, all_tags=tags)


@app.route("/functional_overview")
def functional_overview():
    return render_template(
        "functional_overview.html",
        overview=FUNCTIONAL_OVERVIEW,
    )


@app.route("/prd")
def prd_view():
    return render_template("prd.html", prd=PRD_DATA)


@app.route("/design")
def design_view():
    return render_template("design_overview.html", design=DESIGN_DATA)


@app.route("/storage/local", methods=["GET", "POST"])
def storage_local():
    if request.method == "POST":
        if request.form.get("type") == "disk":
            disk = Disk(
                serial=request.form.get("serial"),
                capacity_gb=int(request.form.get("capacity")),
                temperature=float(request.form.get("temperature", 35)),
                smart_status=request.form.get("smart_status", "OK"),
                health=request.form.get("health", "Healthy"),
                raid_id=request.form.get("raid_id"),
            )
            db.session.add(disk)
            db.session.commit()
            flash("磁盘已添加", "success")
        else:
            raid = RaidArray(
                name=request.form.get("name"),
                level=request.form.get("level"),
                status=request.form.get("status"),
                capacity_total=int(request.form.get("capacity_total")),
                capacity_used=int(request.form.get("capacity_used")),
                notes=request.form.get("notes"),
            )
            db.session.add(raid)
            db.session.commit()
            flash("阵列已创建", "success")

    raids = RaidArray.query.all()
    disks = Disk.query.all()
    return render_template("storage_local.html", raids=raids, disks=disks)


@app.route("/storage/cloud", methods=["GET", "POST"])
def storage_cloud():
    if request.method == "POST":
        target = StorageTarget(
            name=request.form.get("name"),
            target_type=request.form.get("target_type"),
            endpoint=request.form.get("endpoint"),
            bucket=request.form.get("bucket"),
            access_key=request.form.get("access_key"),
            description=request.form.get("description"),
            auth_mode=request.form.get("auth_mode"),
            extra=request.form.get("extra"),
        )
        db.session.add(target)
        db.session.commit()
        flash("云端目标已添加", "success")

    targets = StorageTarget.query.all()
    return render_template("storage_cloud.html", targets=targets)


@app.route("/sync_tasks", methods=["GET", "POST"])
def sync_tasks():
    projects = Project.query.all()
    targets = StorageTarget.query.all()
    if request.method == "POST":
        task = SyncTask(
            name=request.form.get("name"),
            project_id=request.form.get("project_id"),
            source_path=request.form.get("source_path"),
            direction=request.form.get("direction"),
            mode=request.form.get("mode"),
            schedule=request.form.get("schedule"),
            bandwidth_high=int(request.form.get("bandwidth_high", 0) or 0),
            bandwidth_low=int(request.form.get("bandwidth_low", 0) or 0),
            conflict_strategy=request.form.get("conflict_strategy"),
            file_filter=request.form.get("file_filter"),
            status="未启动",
        )
        db.session.add(task)
        db.session.flush()
        selected_targets = request.form.getlist("targets")
        for target_id in selected_targets:
            target = StorageTarget.query.get(int(target_id))
            if target:
                task.targets.append(target)
        db.session.commit()
        log_event("同步", "创建任务", f"{task.name}")
        flash("同步任务已创建", "success")
        return redirect(url_for("sync_tasks"))

    tasks = SyncTask.query.order_by(SyncTask.id.desc()).all()
    return render_template("sync_tasks.html", tasks=tasks, projects=projects, targets=targets)


@app.route("/sync_tasks/<int:task_id>/run", methods=["POST"])
def run_sync(task_id):
    task = SyncTask.query.get_or_404(task_id)
    task.status = "运行中"
    task.last_run = datetime.utcnow()
    task.next_run = task.last_run + timedelta(hours=24)
    db.session.commit()
    log_event("同步", "手动执行", f"{task.name} 手动触发")
    flash("同步任务已触发", "info")
    return redirect(url_for("sync_tasks"))


@app.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        user = User(
            username=request.form.get("username"),
            role=request.form.get("role"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
        )
        db.session.add(user)
        db.session.commit()
        log_event("用户", "创建用户", f"{user.username}")
        flash("用户已创建", "success")

    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/logs")
def logs():
    entries = LogEntry.query.order_by(LogEntry.timestamp.desc()).limit(200).all()
    return render_template("logs.html", entries=entries)


@app.route("/policies", methods=["GET", "POST"])
def policies():
    projects = Project.query.all()
    if request.method == "POST":
        project_id = request.form.get("project_id")
        policy = StoragePolicy.query.filter_by(project_id=project_id).first()
        if not policy:
            policy = StoragePolicy(project_id=project_id)
            db.session.add(policy)
        policy.hot_to_warm_days = int(request.form.get("hot_days"))
        policy.warm_to_cold_months = int(request.form.get("warm_months"))
        policy.keep_local_hot = request.form.get("keep_hot") == "on"
        policy.keep_local_warm = request.form.get("keep_warm") == "on"
        policy.keep_local_cold = request.form.get("keep_cold") == "on"
        db.session.commit()
        flash("策略已更新", "success")

    policies = StoragePolicy.query.all()
    return render_template("policies.html", policies=policies, projects=projects)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
