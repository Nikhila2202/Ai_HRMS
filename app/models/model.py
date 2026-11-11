from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey,
    Index, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint,
    func, text
)

from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from sqlalchemy.orm import relationship

from database import Base

from pgvector.sqlalchemy import HALFVEC



# 1. ORGANIZATION AND ACCESS CONTROL (8 TABLES)

class Department(Base):
    __tablename__ = "departments"
    department_id = Column(BigInteger, primary_key=True, autoincrement=True)
    department_name = Column(String, nullable=False, unique=True)
    department_code = Column(String, nullable=True, unique=True)
    parent_department_id = Column(BigInteger, ForeignKey("departments.department_id"))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    parent = relationship("Department", remote_side=[department_id], back_populates="children")
    children = relationship("Department", back_populates="parent")
    employees = relationship("Employee", back_populates="department_obj")



class Employee(Base):
    __tablename__ = "employees"
    employee_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_code = Column(String, nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=True)  # Legacy/display field retained by the document
    job_title = Column(String, nullable=True)
    hire_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    department_id = Column(BigInteger, ForeignKey("departments.department_id"), nullable=True)
    manager_employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=True)

    department_obj = relationship("Department", back_populates="employees")
    manager = relationship("Employee", remote_side=[employee_id], back_populates="direct_reports")
    direct_reports = relationship("Employee", back_populates="manager")
    user = relationship("User", back_populates="employee", uselist=False)
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    document_requests = relationship("HRDocumentRequest", foreign_keys="HRDocumentRequest.employee_id", back_populates="employee")
    timesheets = relationship("Timesheet", back_populates="employee")

class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=True, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    employee = relationship("Employee", back_populates="user")
    roles = relationship("UserRole", back_populates="user")
    conversations = relationship("AIConversation", back_populates="user")
    from sqlalchemy.orm import relationship

# Inside your existing User class

roles = relationship(
    "UserRole",
    back_populates="user",
    cascade="all, delete-orphan"
)

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    users = relationship("UserRole", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role")
    # Inside your existing Role class

users = relationship(
    "UserRole",
    back_populates="role"
)

permissions = relationship(
    "RolePermission",
    back_populates="role",
    cascade="all, delete-orphan"
)

class Permission(Base):
    __tablename__ = "permissions"
    permission_id = Column(BigInteger, primary_key=True, autoincrement=True)
    permission_code = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    roles = relationship("RolePermission", back_populates="permission")
    # Inside your existing Permission class
# Inside your existing Permission class

role_permissions = relationship(
    "RolePermission",
    back_populates="permission"
)


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(BigInteger, ForeignKey("roles.role_id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    # Inside your existing UserRole class

user = relationship(
    "User",
    back_populates="roles"
)

role = relationship(
    "Role",
    back_populates="users"
)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(BigInteger, ForeignKey("roles.role_id"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("permissions.permission_id"), primary_key=True)
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")
    # Inside your existing RolePermission class

role = relationship(
    "Role",
    back_populates="permissions"
)

permission = relationship(
    "Permission",
    back_populates="role_permissions"
)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    audit_log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    actor_user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    details = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    __table_args__ = (
        Index("idx_audit_logs_actor", "actor_user_id"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
    )

# 2. LEAVE MANAGEMENT (7 TABLES)

class LeaveType(Base):
    __tablename__ = "leave_types"
    leave_type_id = Column(BigInteger, primary_key=True, autoincrement=True)
    leave_type_code = Column(String, nullable=False, unique=True)
    leave_type_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_paid = Column(Boolean, nullable=False, server_default=text("true"))
    requires_approval = Column(Boolean, nullable=False, server_default=text("true"))
    min_notice_calendar_days = Column(Integer, nullable=False, server_default=text("0"))
    max_consecutive_days = Column(Numeric, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    entitlement_rules = relationship("LeaveEntitlementRule", back_populates="leave_type")
    balances = relationship("LeaveBalance", back_populates="leave_type_obj")
    requests = relationship("LeaveRequest", back_populates="leave_type_obj")
    __table_args__ = (
        CheckConstraint("min_notice_calendar_days >= 0", name="chk_leave_type_notice"),
        CheckConstraint("max_consecutive_days IS NULL OR max_consecutive_days > 0", name="chk_leave_type_max_days"),
    )


class LeaveEntitlementRule(Base):
    __tablename__ = "leave_entitlement_rules"
    entitlement_rule_id = Column(BigInteger, primary_key=True, autoincrement=True)
    leave_type_id = Column(BigInteger, ForeignKey("leave_types.leave_type_id"), nullable=False)
    employment_category = Column(String, nullable=False, server_default=text("'all'"))
    entitlement_days = Column(Numeric, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    leave_type = relationship("LeaveType", back_populates="entitlement_rules")
    __table_args__ = (
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="chk_entitlement_rule_dates"),
        CheckConstraint("entitlement_days >= 0", name="chk_entitlement_rule_days"),
        Index("idx_entitlement_rules_lookup", "leave_type_id", "employment_category", "effective_from"),
    )

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    leave_balance_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=False)
    leave_type = Column(String, ForeignKey("leave_types.leave_type_code"), nullable=False)
    entitlement_days = Column(Numeric, nullable=False, server_default=text("0"))
    used_days = Column(Numeric, nullable=False, server_default=text("0"))
    balance_year = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    employee = relationship("Employee", back_populates="leave_balances")
    leave_type_obj = relationship("LeaveType", back_populates="balances")
    transactions = relationship("LeaveTransaction", back_populates="leave_balance")
    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type", "balance_year", name="uq_employee_leave_year"),
        CheckConstraint("entitlement_days >= 0", name="chk_entitlement_days"),
        CheckConstraint("used_days >= 0 AND used_days <= entitlement_days", name="chk_used_days"),
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    leave_request_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=False)
    leave_type = Column(String, ForeignKey("leave_types.leave_type_code"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Numeric, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, server_default=text("'pending'"))
    submitted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    employee = relationship("Employee", back_populates="leave_requests")
    leave_type_obj = relationship("LeaveType", back_populates="requests")
    approvals = relationship("LeaveApproval", back_populates="leave_request")
    transactions = relationship("LeaveTransaction", back_populates="leave_request")
    __table_args__ = (
        CheckConstraint("days_requested > 0", name="chk_days_requested"),
        CheckConstraint("end_date >= start_date", name="chk_leave_dates"),
        CheckConstraint("status IN ('pending','approved','rejected','cancelled')", name="chk_leave_request_status"),
        Index("idx_leave_requests_dates", "start_date", "end_date"),
        Index("idx_leave_requests_employee_status", "employee_id", "status"),
    )

class LeaveApproval(Base):
    __tablename__ = "leave_approvals"
    leave_approval_id = Column(BigInteger, primary_key=True, autoincrement=True)
    leave_request_id = Column(BigInteger, ForeignKey("leave_requests.leave_request_id"), nullable=False)
    approver_employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=False)
    decision = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    leave_request = relationship("LeaveRequest", back_populates="approvals")
    __table_args__ = (Index("idx_leave_approvals_request", "leave_request_id", "decided_at"),)


class LeaveTransaction(Base):
    __tablename__ = "leave_transactions"
    leave_transaction_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=False)
    leave_balance_id = Column(BigInteger, ForeignKey("leave_balances.leave_balance_id"), nullable=False)
    leave_request_id = Column(BigInteger, ForeignKey("leave_requests.leave_request_id"), nullable=True)
    transaction_type = Column(String, nullable=False)
    days_delta = Column(Numeric, nullable=False)
    notes = Column(Text, nullable=True)
    actor_user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    leave_balance = relationship("LeaveBalance", back_populates="transactions")
    leave_request = relationship("LeaveRequest", back_populates="transactions")
    __table_args__ = (
        CheckConstraint("days_delta <> 0", name="chk_leave_transaction_nonzero"),
        CheckConstraint("transaction_type IN ('accrual','usage','adjustment','reversal')", name="chk_leave_transaction_type"),
        Index("idx_leave_transactions_balance", "leave_balance_id", "created_at"),
        Index("idx_leave_transactions_employee", "employee_id", "created_at"),
        Index("idx_leave_transactions_request", "leave_request_id", postgresql_where=text("leave_request_id IS NOT NULL")),
    )


class PublicHoliday(Base):
    __tablename__ = "public_holidays"
    public_holiday_id = Column(BigInteger, primary_key=True, autoincrement=True)
    holiday_date = Column(Date, nullable=False)
    holiday_name = Column(String, nullable=False)
    country_code = Column(String, nullable=False, server_default=text("'AE'"))
    region = Column(String, nullable=False, server_default=text("'all'"))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint("holiday_date", "country_code", "region", name="uq_public_holiday"),
        Index("idx_public_holidays_date", "holiday_date", postgresql_where=text("is_active = true")),
    )

# 3. HR DOCUMENT MANAGEMENT (3 TABLES)

class HRDocumentType(Base):
    __tablename__ = "hr_document_types"
    document_type_id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_type_code = Column(String, nullable=False, unique=True)
    document_type_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    requires_hr_approval = Column(Boolean, nullable=False, server_default=text("true"))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class HRDocumentRequest(Base):
    __tablename__ = "hr_document_requests"
    document_request_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=False)
    document_type = Column(String, ForeignKey("hr_document_types.document_type_code"), nullable=False)
    purpose = Column(Text, nullable=True)
    status = Column(String, nullable=False, server_default=text("'pending'"))
    requested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_by_employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(Text, nullable=True)
    document_reference = Column(String, nullable=True)
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="document_requests")
    processor = relationship("Employee", foreign_keys=[processed_by_employee_id])
    document_type_obj = relationship("HRDocumentType")
    history = relationship("HRDocumentRequestHistory", back_populates="request")
    __table_args__ = (
        Index("idx_document_requests_employee_status", "employee_id", "status"),
        Index("idx_document_requests_processor", "processed_by_employee_id", postgresql_where=text("processed_by_employee_id IS NOT NULL")),
        Index("idx_document_requests_requested_at", "requested_at"),
    )


class HRDocumentRequestHistory(Base):
    __tablename__ = "hr_document_request_history"
    history_id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_request_id = Column(BigInteger, ForeignKey("hr_document_requests.document_request_id"), nullable=False)
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    action_by_user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    comments = Column(Text, nullable=True)
    action_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    request = relationship("HRDocumentRequest", back_populates="history")
    __table_args__ = (Index("idx_document_history_request", "document_request_id", "action_at"),)


# 4. TIMESHEET MANAGEMENT (3 TABLES)

class Timesheet(Base):
    __tablename__ = "timesheets"
    timesheet_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String, nullable=False, server_default=text("'draft'"))
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    total_hours = Column(Numeric, nullable=False, server_default=text("0"))
    employee_comments = Column(Text, nullable=True)
    reviewer_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    employee = relationship("Employee", back_populates="timesheets")
    entries = relationship("TimesheetEntry", back_populates="timesheet")
    approvals = relationship("TimesheetApproval", back_populates="timesheet")
    __table_args__ = (
        UniqueConstraint("employee_id", "period_start", name="uq_timesheet_employee_period"),
        CheckConstraint("period_end = period_start + 6", name="chk_timesheet_period"),
        CheckConstraint("status IN ('draft','submitted','approved','rejected')", name="chk_timesheet_status"),
        CheckConstraint("total_hours >= 0", name="chk_timesheet_total_hours"),
        Index("idx_timesheets_employee_status", "employee_id", "status"),
        Index("idx_timesheets_period", "period_start", "period_end"),
    )


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"
    timesheet_entry_id = Column(BigInteger, primary_key=True, autoincrement=True)
    timesheet_id = Column(BigInteger, ForeignKey("timesheets.timesheet_id"), nullable=False)
    work_date = Column(Date, nullable=False)
    hours_worked = Column(Numeric, nullable=False)
    task_description = Column(Text, nullable=True)
    project_code = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    timesheet = relationship("Timesheet", back_populates="entries")
    __table_args__ = (
        UniqueConstraint("timesheet_id", "work_date", name="uq_timesheet_work_date"),
        CheckConstraint("hours_worked >= 0 AND hours_worked <= 24", name="chk_timesheet_entry_hours"),
        Index("idx_timesheet_entries_work_date", "work_date"),
    )

class TimesheetApproval(Base):
    __tablename__ = "timesheet_approvals"
    timesheet_approval_id = Column(BigInteger, primary_key=True, autoincrement=True)
    timesheet_id = Column(BigInteger, ForeignKey("timesheets.timesheet_id"), nullable=False)
    approver_employee_id = Column(BigInteger, ForeignKey("employees.employee_id"), nullable=False)
    decision = Column(String, nullable=False)
    comments = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    timesheet = relationship("Timesheet", back_populates="approvals")
    __table_args__ = (
        CheckConstraint("decision IN ('approved','rejected')", name="chk_timesheet_approval_decision"),
        Index("idx_timesheet_approvals_timesheet", "timesheet_id", "decided_at"),
    )


# 5. AI ASSISTANT AND CONVERSATION (3 TABLES)

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    conversation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    title = Column(String, nullable=True)
    status = Column(String, nullable=False, server_default=text("'active'"))
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    conversation_metadata = Column("metadata", JSONB,nullable=False, server_default=text("'{}'::jsonb"))
    user = relationship("User", back_populates="conversations")
    messages = relationship("AIMessage", back_populates="conversation")
    tool_executions = relationship("AIToolExecution", back_populates="conversation")
    __table_args__ = (Index("idx_ai_conversations_user_recent", "user_id", "started_at"),)



class AIMessage(Base):
    __tablename__ = "ai_messages"

    message_id = Column(BigInteger, primary_key=True, autoincrement=True)

    conversation_id = Column(
        BigInteger,
        ForeignKey("ai_conversations.conversation_id"),
        nullable=False
    )

    sender_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    model_name = Column(String, nullable=True)
    token_count = Column(Integer, nullable=True)

    # Python attribute: message_metadata
    # PostgreSQL column name remains: metadata
    message_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    conversation = relationship(
        "AIConversation",
        back_populates="messages"
    )

    tool_executions = relationship(
        "AIToolExecution",
        back_populates="message"
    )

    __table_args__ = (
        Index(
            "idx_ai_messages_conversation_time",
            "conversation_id",
            "created_at"
        ),
    )

class AIToolExecution(Base):
    __tablename__ = "ai_tool_executions"
    tool_execution_id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, ForeignKey("ai_conversations.conversation_id"), nullable=False)
    message_id = Column(BigInteger, ForeignKey("ai_messages.message_id"), nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    tool_name = Column(String, nullable=False)
    input_arguments = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    execution_status = Column(String, nullable=False, server_default=text("'started'"))
    result_summary = Column(Text, nullable=True)
    error_code = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    conversation = relationship("AIConversation", back_populates="tool_executions")
    message = relationship("AIMessage", back_populates="tool_executions")
    __table_args__ = (
        Index("idx_ai_tool_executions_conversation", "conversation_id", "started_at"),
        Index("idx_ai_tool_executions_status", "execution_status", "started_at"),
        Index("idx_ai_tool_executions_user", "user_id", "started_at"),
    )


# 6. HR POLICY KNOWLEDGE BASE / RAG (3 TABLES)

class HRPolicy(Base):
    __tablename__ = "hr_policies"
    policy_id = Column(BigInteger, primary_key=True, autoincrement=True)
    policy_code = Column(String, nullable=False, unique=True)
    policy_title = Column(String, nullable=False)
    policy_category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    department_id = Column(BigInteger, ForeignKey("departments.department_id"), nullable=True)
    owner_user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    status = Column(String, nullable=False, server_default=text("'draft'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    versions = relationship("HRPolicyVersion", back_populates="policy")
    __table_args__ = (
        Index("idx_hr_policies_category", "policy_category"),
        Index("idx_hr_policies_department", "department_id"),
        Index("idx_hr_policies_status", "status"),
    )

class HRPolicyVersion(Base):
    __tablename__ = "hr_policy_versions"
    policy_version_id = Column(BigInteger, primary_key=True, autoincrement=True)
    policy_id = Column(BigInteger, ForeignKey("hr_policies.policy_id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    version_label = Column(String, nullable=True)
    status = Column(String, nullable=False, server_default=text("'draft'"))
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    source_file_name = Column(String, nullable=True)
    source_reference = Column(Text, nullable=True)
    change_summary = Column(Text, nullable=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    policy = relationship("HRPolicy", back_populates="versions")
    chunks = relationship("HRPolicyChunk", back_populates="policy_version")
    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uq_hr_policy_version_number"),
        CheckConstraint("effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from", name="chk_hr_policy_version_dates"),
        Index("idx_hr_policy_versions_effective_dates", "effective_from", "effective_to"),
        Index("idx_hr_policy_versions_policy", "policy_id", "version_number"),
        Index("idx_hr_policy_versions_status", "status"),
    )



class HRPolicyChunk(Base):
    __tablename__ = "hr_policy_chunks"

    policy_chunk_id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    policy_version_id = Column(
        BigInteger,
        ForeignKey("hr_policy_versions.policy_version_id"),
        nullable=False
    )

    chunk_number = Column(Integer, nullable=False)
    section_heading = Column(String, nullable=True)
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    source_reference = Column(Text, nullable=True)

    embedding_model = Column(
        String,
        nullable=False,
        server_default=text("'gemini-embedding-001'")
    )

    embedding_dimensions = Column(
        SmallInteger,
        nullable=False,
        server_default=text("3072")
    )

    # Temporary storage until PostgreSQL pgvector is installed
    embedding = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    search_vector = Column(TSVECTOR, nullable=True)

    policy_version = relationship(
        "HRPolicyVersion",
        back_populates="chunks"
    )

    __table_args__ = (
        UniqueConstraint(
            "policy_version_id",
            "chunk_number",
            name="uq_hr_policy_chunk_number"
        ),
        Index("idx_hr_policy_chunks_version", "policy_version_id"),
        Index(
            "idx_hr_policy_chunks_search_vector",
            "search_vector",
            postgresql_using="gin"
        ),
    )

