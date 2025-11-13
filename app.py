import os
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nas_demo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("NAS_DEMO_SECRET", "nas-demo-secret")

db = SQLAlchemy(app)


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

    total_capacity = sum(d.capacity_gb for d in disks)
    used_capacity = sum(r.capacity_used or 0 for r in RaidArray.query.all())
    hot_files = len([f for f in files if f.storage_state == "Hot"])
    warm_files = len([f for f in files if f.storage_state == "Warm"])
    cold_files = len([f for f in files if f.storage_state == "Cold"])

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
