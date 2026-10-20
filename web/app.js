/**
 * PAWS Frontend Application
 * Согласовано с моделями src/models.py, бизнес-логикой src/app.py и требованиями ТЗ.
 */

const STORAGE_KEY = "paws_webapp_state_v1";

// Начальные демонстрационные данные, соответствующие seed_demo_data в src/main.py
function getInitialDemoData() {
  return {
    employees: [
      {
        id: "E001",
        full_name: "Иванов Иван Иванович",
        position: "Системный администратор",
        department: "ИТ-отдел",
        hire_date: "2023-02-15",
        contact: "ivanov@paws.local, +7 (900) 111-22-33",
        active: true
      },
      {
        id: "E002",
        full_name: "Петров Пётр Петрович",
        position: "Руководитель смены",
        department: "Производственный отдел",
        hire_date: "2023-05-10",
        contact: "petrov@paws.local, +7 (900) 222-33-44",
        active: true
      },
      {
        id: "E003",
        full_name: "Сидоров Сидор Сидорович",
        position: "Дежурный инженер",
        department: "Производственный отдел",
        hire_date: "2024-01-20",
        contact: "sidorov@paws.local, +7 (900) 333-44-55",
        active: true
      }
    ],
    shifts: [
      {
        id: "SH-1001",
        employee_id: "E003",
        shift_date: "2025-05-01",
        time_start: "08:00",
        time_end: "16:00",
        hours: 8.0,
        is_night: false,
        created_at: "2025-05-01 08:05",
        updated_at: "2025-05-01 16:02",
        works: [
          { id: "W-1", description: "Проверка серверного оборудования и журналов событий" },
          { id: "W-2", description: "Регламентное обслуживание узлов связи" }
        ]
      },
      {
        id: "SH-1002",
        employee_id: "E003",
        shift_date: "2025-05-02",
        time_start: "22:00",
        time_end: "06:00",
        hours: 8.0,
        is_night: true,
        created_at: "2025-05-02 22:00",
        updated_at: "2025-05-03 06:05",
        works: [
          { id: "W-3", description: "Ночное дежурство и мониторинг инфраструктуры" },
          { id: "W-4", description: "Резервное копирование баз данных" }
        ]
      },
      {
        id: "SH-1003",
        employee_id: "E002",
        shift_date: "2025-05-02",
        time_start: "09:00",
        time_end: "18:00",
        hours: 9.0,
        is_night: false,
        created_at: "2025-05-02 09:00",
        updated_at: "2025-05-02 18:10",
        works: [
          { id: "W-5", description: "Контроль выполнения плановых работ по смене" },
          { id: "W-6", description: "Согласование графиков дежурств" }
        ]
      }
    ],
    users: [
      { username: "ivanov", password_plain_demo: "admin123", password_hash: "pbkdf2_sha256$260000$9f8a1b...e41c", employee_id: "E001", role: "admin" },
      { username: "petrov", password_plain_demo: "manager123", password_hash: "pbkdf2_sha256$260000$3c7d2e...a90b", employee_id: "E002", role: "manager" },
      { username: "sidorov", password_plain_demo: "emp123", password_hash: "pbkdf2_sha256$260000$7b1e4a...f12d", employee_id: "E003", role: "employee" }
    ],
    reportsHistory: [
      {
        id: "REP-001",
        type: "Сводный отчёт за период",
        period: "2025-05-01 — 2025-05-05",
        filter: "Все сотрудники",
        created_at: "2025-05-05 18:30",
        author: "petrov (Руководитель)",
        format: "PDF"
      }
    ],
    settings: {
      orgName: "ВолгГТУ, кафедра «ПОАС»",
      defaultFormat: "pdf",
      maxShiftHours: 24,
      updatedAt: "2025-05-01 10:00"
    }
  };
}

let state = loadState();
let currentUser = null;
let lastGeneratedReport = null;
let pendingConfirmAction = null;

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.warn("Не удалось прочитать localStorage, используются демо-данные.");
  }
  return getInitialDemoData();
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.warn("Ошибка сохранения состояния в localStorage.");
  }
}

// Утилита уведомлений (ТЗ п. 4.5)
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// Очистка и показ ошибки конкретного поля (ТЗ п. 4.5)
function clearFormErrors(formElement) {
  formElement.querySelectorAll(".form-group.has-error").forEach(fg => fg.classList.remove("has-error"));
  formElement.querySelectorAll(".field-error").forEach(el => (el.textContent = ""));
}

function setFieldError(groupId, errorId, message) {
  const group = document.getElementById(groupId);
  const err = document.getElementById(errorId);
  if (group) group.classList.add("has-error");
  if (err) err.textContent = message;
}

// Расчет продолжительности смены (с учетом ночных смен +1 сутки по таблице в п. 7.1 ТЗ)
function calculateShiftHours(startStr, endStr, allowNight) {
  if (!startStr || !endStr) return { valid: false, hours: 0, isNight: false };
  const [sh, sm] = startStr.split(":").map(Number);
  const [eh, em] = endStr.split(":").map(Number);
  const startMinutes = sh * 60 + sm;
  let endMinutes = eh * 60 + em;
  let isNight = false;

  if (endMinutes <= startMinutes) {
    if (allowNight) {
      endMinutes += 24 * 60;
      isNight = true;
    } else {
      return { valid: false, hours: 0, isNight: false };
    }
  }

  const diffHours = Number(((endMinutes - startMinutes) / 60).toFixed(2));
  return { valid: diffHours > 0 && diffHours <= state.settings.maxShiftHours, hours: diffHours, isNight };
}

// Ролевые подписи
function getRoleLabel(role) {
  const map = {
    admin: "Администратор",
    manager: "Руководитель",
    employee: "Сотрудник"
  };
  return map[role] || role;
}

function getEmployeeById(empId) {
  return state.employees.find(e => e.id === empId) || null;
}

// ================= АВТОРИЗАЦИЯ И РАЗГРАНИЧЕНИЕ ПРАВ (ТЗ п. 4.2.1, 4.4, 4.5) =================
function initAuth() {
  const loginForm = document.getElementById("login-form");
  const generalError = document.getElementById("login-general-error");

  // Быстрое заполнение демо-аккаунтов
  document.querySelectorAll("[data-demo-user]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.getElementById("login-username").value = btn.dataset.demoUser;
      document.getElementById("login-password").value = btn.dataset.demoPass;
      clearFormErrors(loginForm);
      generalError.hidden = true;
    });
  });

  loginForm.addEventListener("submit", e => {
    e.preventDefault();
    clearFormErrors(loginForm);
    generalError.hidden = true;

    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;

    let hasErr = false;
    if (!username) {
      setFieldError("fg-login-username", "err-login-username", "Поле «Имя пользователя» обязательно для заполнения");
      hasErr = true;
    }
    if (!password) {
      setFieldError("fg-login-password", "err-login-password", "Поле «Пароль» обязательно для заполнения");
      hasErr = true;
    }
    if (hasErr) return;

    const foundUser = state.users.find(
      u => u.username.toLowerCase() === username.toLowerCase() && u.password_plain_demo === password
    );

    // Штатное поведение при неверном пароле (ТЗ п. 7.1)
    if (!foundUser) {
      generalError.textContent = "Ошибка авторизации: неверное имя пользователя или пароль.";
      generalError.hidden = false;
      return;
    }

    const emp = getEmployeeById(foundUser.employee_id);
    if (emp && !emp.active) {
      generalError.textContent = "Доступ запрещён: запись сотрудника деактивирована.";
      generalError.hidden = false;
      return;
    }

    currentUser = foundUser;
    enterAuthenticatedApp();
  });

  document.getElementById("btn-logout").addEventListener("click", () => {
    currentUser = null;
    document.getElementById("app-layout").hidden = true;
    document.getElementById("auth-screen").hidden = false;
    document.getElementById("login-password").value = "";
    showToast("Вы вышли из системы", "success");
  });
}

function enterAuthenticatedApp() {
  document.getElementById("auth-screen").hidden = true;
  document.getElementById("app-layout").hidden = false;

  const emp = getEmployeeById(currentUser.employee_id);
  document.getElementById("topbar-user-name").textContent = emp ? emp.full_name : currentUser.username;
  document.getElementById("topbar-user-role").textContent = getRoleLabel(currentUser.role);

  // Скрытие недоступных разделов и кнопок по роли (ТЗ п. 4.5)
  document.querySelectorAll("[data-role-allowed]").forEach(el => {
    const allowed = el.dataset.roleAllowed.split(",").map(s => s.trim());
    el.hidden = !allowed.includes(currentUser.role);
  });

  populateSelectControls();
  renderAllSections();
  switchSection("dashboard");
  showToast(`Добро пожаловать, ${emp ? emp.full_name : currentUser.username}!`, "success");
}

// ================= НАВИГАЦИЯ =================
function switchSection(sectionKey) {
  const titles = {
    dashboard: "Главная страница",
    employees: "Сотрудники",
    shifts: "Рабочие смены и выполненные работы",
    search: "Поиск и просмотр информации",
    reports: "Формирование и экспорт отчетов",
    admin: "Администрирование системы"
  };

  document.querySelectorAll(".page-section").forEach(sec => {
    sec.hidden = sec.id !== `sec-${sectionKey}`;
  });

  document.querySelectorAll(".nav-link").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.section === sectionKey);
  });

  document.getElementById("current-page-title").textContent = titles[sectionKey] || "PAWS";
}

function initNavigation() {
  document.querySelectorAll(".nav-link").forEach(btn => {
    btn.addEventListener("click", () => switchSection(btn.dataset.section));
  });

  document.querySelectorAll("[data-goto]").forEach(btn => {
    btn.addEventListener("click", () => switchSection(btn.dataset.goto));
  });

  // Быстрые переходы с главного экрана (ТЗ п. 4.5: не более 3 переходов)
  document.getElementById("qa-create-shift").addEventListener("click", () => {
    switchSection("shifts");
    document.getElementById("shift-date").focus();
  });

  document.getElementById("qa-search-shifts").addEventListener("click", () => {
    switchSection("search");
    document.getElementById("search-work-text").focus();
  });

  document.getElementById("qa-build-report").addEventListener("click", () => {
    switchSection("reports");
  });
}

// ================= ЗАПОЛНЕНИЕ ВЫПАДАЮЩИХ СПИСКОВ =================
function populateSelectControls() {
  const shiftEmpSelect = document.getElementById("shift-emp");
  const searchEmpSelect = document.getElementById("search-emp");
  const repEmpSelect = document.getElementById("rep-emp");
  const repDeptSelect = document.getElementById("rep-dept");
  const usrEmpSelect = document.getElementById("usr-emp");

  shiftEmpSelect.innerHTML = "";
  searchEmpSelect.innerHTML = '<option value="all">Все сотрудники</option>';
  repEmpSelect.innerHTML = '<option value="all">Все сотрудники</option>';
  usrEmpSelect.innerHTML = "";

  const departments = new Set();

  state.employees.forEach(emp => {
    departments.add(emp.department);

    const label = `${emp.full_name} (${emp.id})${emp.active ? "" : " [Деактивирован]"}`;

    // Для создания смены: сотрудник видит только себя, остальные — всех активных
    if (emp.active) {
      if (!currentUser || currentUser.role !== "employee" || currentUser.employee_id === emp.id) {
        const optShift = new Option(label, emp.id);
        shiftEmpSelect.add(optShift);
      }
    }

    searchEmpSelect.add(new Option(label, emp.id));
    repEmpSelect.add(new Option(label, emp.id));
    usrEmpSelect.add(new Option(label, emp.id));
  });

  repDeptSelect.innerHTML = '<option value="all">Все подразделения</option>';
  departments.forEach(dept => {
    repDeptSelect.add(new Option(dept, dept));
  });
}

// ================= 1. ГЛАВНАЯ СТРАНИЦА (ДАШБОРД) =================
function renderDashboard() {
  const activeEmps = state.employees.filter(e => e.active).length;
  document.getElementById("stat-active-employees").textContent = activeEmps;
  document.getElementById("stat-total-employees").textContent = `Всего в базе: ${state.employees.length}`;

  document.getElementById("stat-total-shifts").textContent = state.shifts.length;

  const totalHours = state.shifts.reduce((acc, s) => acc + Number(s.hours || 0), 0);
  document.getElementById("stat-total-hours").textContent = totalHours.toFixed(2);

  const totalWorks = state.shifts.reduce((acc, s) => acc + (s.works ? s.works.length : 0), 0);
  document.getElementById("stat-total-works").textContent = totalWorks;

  const tbody = document.getElementById("dashboard-recent-shifts");
  tbody.innerHTML = "";

  const recent = [...state.shifts].slice(-5).reverse();
  if (recent.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">Записи о рабочих сменах отсутствуют.</td></tr>';
    return;
  }

  recent.forEach(s => {
    const emp = getEmployeeById(s.employee_id);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${s.id}</code></td>
      <td>${emp ? emp.full_name : s.employee_id}</td>
      <td>${s.shift_date}</td>
      <td>${s.time_start} — ${s.time_end} ${s.is_night ? '<span class="role-badge">+1 сут.</span>' : ""}</td>
      <td><strong>${Number(s.hours).toFixed(2)} ч.</strong></td>
      <td>${s.works.map(w => w.description).join("; ")}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ================= 2. СОТРУДНИКИ (ТЗ п. 4.2.2, 5.2 п.1) =================
function renderEmployees() {
  const query = document.getElementById("filter-emp-query").value.trim().toLowerCase();
  const statusFilter = document.getElementById("filter-emp-status").value;
  const tbody = document.getElementById("employees-table-body");
  tbody.innerHTML = "";

  const filtered = state.employees.filter(emp => {
    const matchesQuery =
      !query ||
      emp.id.toLowerCase().includes(query) ||
      emp.full_name.toLowerCase().includes(query) ||
      emp.position.toLowerCase().includes(query) ||
      emp.department.toLowerCase().includes(query);

    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && emp.active) ||
      (statusFilter === "inactive" && !emp.active);

    return matchesQuery && matchesStatus;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7">По заданным параметрам сотрудники не найдены.</td></tr>';
    return;
  }

  const isAdmin = currentUser && currentUser.role === "admin";

  filtered.forEach(emp => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${emp.id}</code></td>
      <td><strong>${emp.full_name}</strong></td>
      <td>${emp.position}<br><small class="text-muted">${emp.department}</small></td>
      <td>${emp.hire_date}</td>
      <td>${emp.contact || "—"}</td>
      <td>
        <span class="status-pill ${emp.active ? "status-active" : "status-inactive"}">
          ${emp.active ? "Активен" : "Деактивирован"}
        </span>
      </td>
      <td>
        ${
          isAdmin
            ? `<div class="table-actions">
                <button type="button" class="btn btn-outline btn-sm" data-edit-emp="${emp.id}">Изменить</button>
                <button type="button" class="btn btn-danger btn-sm" data-delete-emp="${emp.id}">Удалить</button>
              </div>`
            : '<span class="text-muted">Только просмотр</span>'
        }
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll("[data-edit-emp]").forEach(btn => {
    btn.addEventListener("click", () => startEditEmployee(btn.dataset.editEmp));
  });

  tbody.querySelectorAll("[data-delete-emp]").forEach(btn => {
    btn.addEventListener("click", () => confirmDeleteOrDeactivateEmployee(btn.dataset.deleteEmp));
  });
}

function startEditEmployee(empId) {
  const emp = getEmployeeById(empId);
  if (!emp) return;

  document.getElementById("emp-edit-mode").value = "edit";
  document.getElementById("employee-form-title").textContent = `Редактирование: ${emp.id}`;
  document.getElementById("btn-cancel-emp-edit").hidden = false;

  const idInput = document.getElementById("emp-id");
  idInput.value = emp.id;
  idInput.disabled = true;

  document.getElementById("emp-fullname").value = emp.full_name;
  document.getElementById("emp-position").value = emp.position;
  document.getElementById("emp-department").value = emp.department;
  document.getElementById("emp-hiredate").value = emp.hire_date;
  document.getElementById("emp-status").value = String(emp.active);
  document.getElementById("emp-contact").value = emp.contact || "";
}

function resetEmployeeForm() {
  const form = document.getElementById("employee-form");
  form.reset();
  clearFormErrors(form);
  document.getElementById("emp-edit-mode").value = "create";
  document.getElementById("employee-form-title").textContent = "Добавление сотрудника";
  document.getElementById("btn-cancel-emp-edit").hidden = true;
  document.getElementById("emp-id").disabled = false;
}

function confirmDeleteOrDeactivateEmployee(empId) {
  const emp = getEmployeeById(empId);
  if (!emp) return;

  const hasShifts = state.shifts.some(s => s.employee_id === empId);
  const message = hasShifts
    ? `У сотрудника ${emp.full_name} (${emp.id}) имеются сохранённые рабочие смены. В соответствии с ТЗ (п. 5.2 п.1) запись будет деактивирована с сохранением истории смен для отчётов. Подтверждаете операцию?`
    : `Вы действительно хотите удалить запись о сотруднике ${emp.full_name} (${emp.id})?`;

  openConfirmModal(message, () => {
    if (hasShifts) {
      emp.active = false;
      showToast(`Сотрудник ${emp.full_name} деактивирован. История смен сохранена.`, "success");
    } else {
      state.employees = state.employees.filter(e => e.id !== empId);
      showToast(`Запись сотрудника ${emp.full_name} удалена.`, "success");
    }
    saveState();
    populateSelectControls();
    renderAllSections();
  });
}

function initEmployeesSection() {
  const form = document.getElementById("employee-form");

  document.getElementById("btn-cancel-emp-edit").addEventListener("click", resetEmployeeForm);
  document.getElementById("filter-emp-query").addEventListener("input", renderEmployees);
  document.getElementById("filter-emp-status").addEventListener("change", renderEmployees);

  form.addEventListener("submit", e => {
    e.preventDefault();
    clearFormErrors(form);

    const mode = document.getElementById("emp-edit-mode").value;
    const id = document.getElementById("emp-id").value.trim();
    const fullName = document.getElementById("emp-fullname").value.trim();
    const position = document.getElementById("emp-position").value.trim();
    const department = document.getElementById("emp-department").value.trim();
    const hireDate = document.getElementById("emp-hiredate").value;
    const active = document.getElementById("emp-status").value === "true";
    const contact = document.getElementById("emp-contact").value.trim();

    let hasErr = false;
    if (!id) {
      setFieldError("fg-emp-id", "err-emp-id", "Укажите уникальный идентификатор сотрудника");
      hasErr = true;
    } else if (mode === "create" && getEmployeeById(id)) {
      setFieldError("fg-emp-id", "err-emp-id", "Сотрудник с таким ID уже существует в базе");
      hasErr = true;
    }

    if (!fullName) {
      setFieldError("fg-emp-fullname", "err-emp-fullname", "Укажите ФИО сотрудника");
      hasErr = true;
    }
    if (!position) {
      setFieldError("fg-emp-position", "err-emp-position", "Укажите должность сотрудника");
      hasErr = true;
    }
    if (!department) {
      setFieldError("fg-emp-department", "err-emp-department", "Укажите подразделение или отдел");
      hasErr = true;
    }
    if (!hireDate) {
      setFieldError("fg-emp-hiredate", "err-emp-hiredate", "Укажите дату приёма на работу");
      hasErr = true;
    }

    if (hasErr) return;

    if (mode === "create") {
      state.employees.push({
        id,
        full_name: fullName,
        position,
        department,
        hire_date: hireDate,
        contact,
        active
      });
      showToast(`Сотрудник ${fullName} успешно добавлен`, "success");
    } else {
      const emp = getEmployeeById(id);
      if (emp) {
        emp.full_name = fullName;
        emp.position = position;
        emp.department = department;
        emp.hire_date = hireDate;
        emp.contact = contact;
        emp.active = active;
        showToast(`Сведения о сотруднике ${fullName} обновлены`, "success");
      }
    }

    saveState();
    resetEmployeeForm();
    populateSelectControls();
    renderAllSections();
  });
}

// ================= 3. РАБОЧИЕ СМЕНЫ И ВЫПОЛНЕННЫЕ РАБОТЫ (ТЗ п. 4.2.3, 7.1) =================
function updateShiftDurationPreview() {
  const start = document.getElementById("shift-start").value;
  const end = document.getElementById("shift-end").value;
  const allowNight = document.getElementById("shift-allow-night").checked;
  const label = document.getElementById("shift-calculated-hours");

  const res = calculateShiftHours(start, end, allowNight);
  if (!res.valid) {
    label.textContent = "Некорректный интервал";
    label.style.color = "#dc2626";
  } else {
    label.textContent = `${res.hours.toFixed(2)} ч.${res.isNight ? " (ночная смена, +1 сутки)" : ""}`;
    label.style.color = "#0f172a";
  }
}

function renderShifts() {
  const tbody = document.getElementById("shifts-table-body");
  tbody.innerHTML = "";

  const visibleShifts = state.shifts.filter(s => {
    if (!currentUser) return false;
    if (currentUser.role === "employee") {
      return s.employee_id === currentUser.employee_id;
    }
    return true;
  });

  if (visibleShifts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8">Записи о рабочих сменах отсутствуют.</td></tr>';
    return;
  }

  visibleShifts.forEach(s => {
    const emp = getEmployeeById(s.employee_id);
    const worksHtml =
      s.works && s.works.length > 0
        ? `<ul class="works-list">${s.works.map(w => `<li><code>${w.id}</code>: ${w.description}</li>`).join("")}</ul>`
        : "—";

    const canEdit =
      currentUser.role === "admin" ||
      currentUser.role === "manager" ||
      (currentUser.role === "employee" && s.employee_id === currentUser.employee_id);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${s.id}</code></td>
      <td><strong>${emp ? emp.full_name : s.employee_id}</strong></td>
      <td>${s.shift_date}</td>
      <td>${s.time_start} — ${s.time_end} ${s.is_night ? '<span class="role-badge">+1 сут.</span>' : ""}</td>
      <td><strong>${Number(s.hours).toFixed(2)}</strong></td>
      <td>${worksHtml}</td>
      <td><small class="text-muted">${s.updated_at || s.created_at}</small></td>
      <td>
        ${
          canEdit
            ? `<div class="table-actions">
                <button type="button" class="btn btn-outline btn-sm" data-edit-shift="${s.id}">Изменить</button>
                <button type="button" class="btn btn-danger btn-sm" data-delete-shift="${s.id}">Удалить</button>
              </div>`
            : "—"
        }
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll("[data-edit-shift]").forEach(btn => {
    btn.addEventListener("click", () => startEditShift(btn.dataset.editShift));
  });

  tbody.querySelectorAll("[data-delete-shift]").forEach(btn => {
    btn.addEventListener("click", () => confirmDeleteShift(btn.dataset.deleteShift));
  });
}

function startEditShift(shiftId) {
  const s = state.shifts.find(item => item.id === shiftId);
  if (!s) return;

  document.getElementById("shift-edit-id").value = s.id;
  document.getElementById("shift-form-title").textContent = `Редактирование смены ${s.id}`;
  document.getElementById("btn-cancel-shift-edit").hidden = false;

  document.getElementById("shift-emp").value = s.employee_id;
  document.getElementById("shift-date").value = s.shift_date;
  document.getElementById("shift-start").value = s.time_start;
  document.getElementById("shift-end").value = s.time_end;
  document.getElementById("shift-allow-night").checked = Boolean(s.is_night);
  document.getElementById("shift-works").value = (s.works || []).map(w => w.description).join("\n");

  updateShiftDurationPreview();
}

function resetShiftForm() {
  const form = document.getElementById("shift-form");
  form.reset();
  clearFormErrors(form);
  document.getElementById("shift-edit-id").value = "";
  document.getElementById("shift-form-title").textContent = "Регистрация рабочей смены";
  document.getElementById("btn-cancel-shift-edit").hidden = true;
  document.getElementById("shift-calculated-hours").textContent = "0.00 ч.";
}

function confirmDeleteShift(shiftId) {
  openConfirmModal(`Вы действительно хотите удалить запись о рабочей смене ${shiftId}?`, () => {
    state.shifts = state.shifts.filter(s => s.id !== shiftId);
    saveState();
    renderAllSections();
    showToast(`Рабочая смена ${shiftId} удалена`, "success");
  });
}

function initShiftsSection() {
  const form = document.getElementById("shift-form");
  document.getElementById("shift-start").addEventListener("input", updateShiftDurationPreview);
  document.getElementById("shift-end").addEventListener("input", updateShiftDurationPreview);
  document.getElementById("shift-allow-night").addEventListener("change", updateShiftDurationPreview);
  document.getElementById("btn-cancel-shift-edit").addEventListener("click", resetShiftForm);

  form.addEventListener("submit", e => {
    e.preventDefault();
    clearFormErrors(form);

    const editId = document.getElementById("shift-edit-id").value;
    const empId = document.getElementById("shift-emp").value;
    const shiftDate = document.getElementById("shift-date").value;
    const timeStart = document.getElementById("shift-start").value;
    const timeEnd = document.getElementById("shift-end").value;
    const allowNight = document.getElementById("shift-allow-night").checked;
    const worksRaw = document.getElementById("shift-works").value
      .split("\n")
      .map(line => line.trim())
      .filter(Boolean);

    let hasErr = false;

    if (!empId) {
      setFieldError("fg-shift-emp", "err-shift-emp", "Выберите сотрудника");
      hasErr = true;
    }
    if (!shiftDate) {
      setFieldError("fg-shift-date", "err-shift-date", "Укажите дату рабочей смены");
      hasErr = true;
    }
    if (!timeStart) {
      setFieldError("fg-shift-start", "err-shift-start", "Укажите время начала смены");
      hasErr = true;
    }
    if (!timeEnd) {
      setFieldError("fg-shift-end", "err-shift-end", "Укажите время окончания смены");
      hasErr = true;
    }

    // Проверка дублирования смены сотрудника на ту же дату (ТЗ п. 7.1: ошибка «смена уже есть»)
    if (empId && shiftDate) {
      const duplicate = state.shifts.find(
        s => s.employee_id === empId && s.shift_date === shiftDate && s.id !== editId
      );
      if (duplicate) {
        setFieldError("fg-shift-date", "err-shift-date", "Ошибка: смена уже есть у выбранного сотрудника на эту дату");
        hasErr = true;
      }
    }

    const calc = calculateShiftHours(timeStart, timeEnd, allowNight);
    if (timeStart && timeEnd && !calc.valid) {
      setFieldError(
        "fg-shift-end",
        "err-shift-end",
        "Время окончания должно быть позже времени начала (или включите режим ночной смены +1 сутки)"
      );
      hasErr = true;
    }

    if (worksRaw.length === 0) {
      setFieldError("fg-shift-works", "err-shift-works", "Внесите хотя бы одну запись о выполненной работе");
      hasErr = true;
    }

    if (hasErr) return;

    const nowStamp = new Date().toISOString().slice(0, 16).replace("T", " ");
    const worksObjects = worksRaw.map((desc, idx) => ({
      id: `W-${Date.now().toString().slice(-3)}-${idx + 1}`,
      description: desc
    }));

    if (!editId) {
      const newId = `SH-${1000 + state.shifts.length + 1}`;
      state.shifts.push({
        id: newId,
        employee_id: empId,
        shift_date: shiftDate,
        time_start: timeStart,
        time_end: timeEnd,
        hours: calc.hours,
        is_night: calc.isNight,
        created_at: nowStamp,
        updated_at: nowStamp,
        works: worksObjects
      });
      showToast(`Рабочая смена ${newId} успешно сохранена (${calc.hours} ч.)`, "success");
    } else {
      const existing = state.shifts.find(s => s.id === editId);
      if (existing) {
        existing.employee_id = empId;
        existing.shift_date = shiftDate;
        existing.time_start = timeStart;
        existing.time_end = timeEnd;
        existing.hours = calc.hours;
        existing.is_night = calc.isNight;
        existing.updated_at = nowStamp;
        existing.works = worksObjects;
        showToast(`Сведения о рабочей смене ${editId} обновлены`, "success");
      }
    }

    saveState();
    resetShiftForm();
    renderAllSections();
  });
}

// ================= 4. ПОИСК И ПРОСМОТР (ТЗ п. 4.2.4) =================
function renderSearchResults() {
  const empId = document.getElementById("search-emp").value;
  const fromDate = document.getElementById("search-date-from").value;
  const toDate = document.getElementById("search-date-to").value;
  const workQuery = document.getElementById("search-work-text").value.trim().toLowerCase();

  const tbody = document.getElementById("search-results-body");
  tbody.innerHTML = "";

  const results = state.shifts.filter(s => {
    if (empId !== "all" && s.employee_id !== empId) return false;
    if (fromDate && s.shift_date < fromDate) return false;
    if (toDate && s.shift_date > toDate) return false;
    if (workQuery) {
      const hasMatch = (s.works || []).some(w => w.description.toLowerCase().includes(workQuery));
      if (!hasMatch) return false;
    }
    return true;
  });

  if (results.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">По заданным критериям рабочие смены не найдены.</td></tr>';
    return;
  }

  results.forEach(s => {
    const emp = getEmployeeById(s.employee_id);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${s.id}</code></td>
      <td><strong>${emp ? emp.full_name : s.employee_id}</strong><br><small class="text-muted">${emp ? emp.department : ""}</small></td>
      <td>${s.shift_date}</td>
      <td>${s.time_start} — ${s.time_end}</td>
      <td><strong>${Number(s.hours).toFixed(2)} ч.</strong></td>
      <td>${(s.works || []).map(w => w.description).join("; ")}</td>
    `;
    tbody.appendChild(tr);
  });
}

function initSearchSection() {
  document.getElementById("search-form").addEventListener("submit", e => {
    e.preventDefault();
    renderSearchResults();
  });

  document.getElementById("btn-search-reset").addEventListener("click", () => {
    document.getElementById("search-form").reset();
    renderSearchResults();
  });
}

// ================= 5. ОТЧЕТЫ И ЭКСПОРТ (ТЗ п. 4.2.5, 4.2.6, 5.4) =================
function initReportsSection() {
  const repTypeSelect = document.getElementById("rep-type");
  const singleDateGroup = document.getElementById("fg-rep-single-date");
  const startGroup = document.getElementById("fg-rep-start");
  const endGroup = document.getElementById("fg-rep-end");
  const reportForm = document.getElementById("report-form");

  // Установка дат по умолчанию
  document.getElementById("rep-single-date").value = "2025-05-02";
  document.getElementById("rep-start").value = "2025-05-01";
  document.getElementById("rep-end").value = "2025-05-05";

  repTypeSelect.addEventListener("change", () => {
    const isDaily = repTypeSelect.value === "daily";
    singleDateGroup.hidden = !isDaily;
    startGroup.hidden = isDaily;
    endGroup.hidden = isDaily;
  });

  reportForm.addEventListener("submit", e => {
    e.preventDefault();
    clearFormErrors(reportForm);

    const type = repTypeSelect.value;
    const singleDate = document.getElementById("rep-single-date").value;
    const startDate = document.getElementById("rep-start").value;
    const endDate = document.getElementById("rep-end").value;
    const deptFilter = document.getElementById("rep-dept").value;
    const empFilter = document.getElementById("rep-emp").value;

    let hasErr = false;
    let periodStart = startDate;
    let periodEnd = endDate;

    if (type === "daily") {
      if (!singleDate) {
        setFieldError("fg-rep-single-date", "err-rep-single-date", "Выберите календарную дату отчёта");
        hasErr = true;
      }
      periodStart = singleDate;
      periodEnd = singleDate;
    } else {
      if (!startDate) {
        setFieldError("fg-rep-start", "err-rep-start", "Укажите дату начала периода");
        hasErr = true;
      }
      if (!endDate) {
        setFieldError("fg-rep-end", "err-rep-end", "Укажите дату окончания периода");
        hasErr = true;
      }
      if (startDate && endDate && endDate < startDate) {
        setFieldError("fg-rep-end", "err-rep-end", "Дата окончания периода не может быть раньше даты начала");
        hasErr = true;
      }
    }

    if (hasErr) return;

    const rows = state.shifts
      .filter(s => {
        if (s.shift_date < periodStart || s.shift_date > periodEnd) return false;
        if (empFilter !== "all" && s.employee_id !== empFilter) return false;
        if (deptFilter !== "all") {
          const emp = getEmployeeById(s.employee_id);
          if (!emp || emp.department !== deptFilter) return false;
        }
        return true;
      })
      .map(s => {
        const emp = getEmployeeById(s.employee_id);
        return {
          employee_name: emp ? emp.full_name : s.employee_id,
          position: emp ? `${emp.position} (${emp.department})` : "—",
          shift_date: s.shift_date,
          time_start: s.time_start,
          time_end: s.time_end,
          hours: Number(s.hours),
          works_text: (s.works || []).map(w => w.description).join("; ")
        };
      });

    const totalShifts = rows.length;
    const totalHours = rows.reduce((acc, r) => acc + r.hours, 0);
    const nowStr = new Date().toISOString().slice(0, 16).replace("T", " ");
    const typeLabel = type === "daily" ? "Ежедневный отчёт за выбранную дату" : "Сводный отчёт за период";
    const periodLabel = type === "daily" ? singleDate : `${periodStart} — ${periodEnd}`;
    const filterLabel =
      empFilter !== "all"
        ? getEmployeeById(empFilter)?.full_name || empFilter
        : deptFilter !== "all"
        ? `Отдел: ${deptFilter}`
        : "Все сотрудники";

    lastGeneratedReport = {
      id: `REP-${String(state.reportsHistory.length + 1).padStart(3, "0")}`,
      type: typeLabel,
      period: periodLabel,
      filter: filterLabel,
      created_at: nowStr,
      author: `${currentUser.username} (${getRoleLabel(currentUser.role)})`,
      rows,
      totalShifts,
      totalHours
    };

    state.reportsHistory.unshift({
      id: lastGeneratedReport.id,
      type: lastGeneratedReport.type,
      period: lastGeneratedReport.period,
      filter: lastGeneratedReport.filter,
      created_at: lastGeneratedReport.created_at,
      author: lastGeneratedReport.author,
      format: "Сформирован"
    });

    saveState();
    renderReportPreview(lastGeneratedReport);
    renderReportHistory();
    document.getElementById("btn-export-report").disabled = false;
    showToast("Отчёт успешно сформирован", "success");
  });

  document.getElementById("btn-export-report").addEventListener("click", exportCurrentReport);
}

function renderReportPreview(rep) {
  const card = document.getElementById("report-preview-card");
  card.hidden = false;

  document.getElementById("report-doc-title").textContent = `${rep.type} (${rep.id})`;
  document.getElementById("report-doc-timestamp").textContent = `Сформирован: ${rep.created_at}`;
  document.getElementById("rep-meta-type").textContent = rep.type;
  document.getElementById("rep-meta-period").textContent = rep.period;
  document.getElementById("rep-meta-filter").textContent = rep.filter;
  document.getElementById("rep-meta-author").textContent = rep.author;

  const tbody = document.getElementById("report-preview-body");
  const tfoot = document.getElementById("report-preview-foot");
  tbody.innerHTML = "";

  if (rep.rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7">За выбранный период рабочие смены не найдены.</td></tr>';
  } else {
    rep.rows.forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${r.employee_name}</strong></td>
        <td>${r.position}</td>
        <td>${r.shift_date}</td>
        <td>${r.time_start}</td>
        <td>${r.time_end}</td>
        <td>${r.hours.toFixed(2)}</td>
        <td>${r.works_text}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  tfoot.innerHTML = `
    <tr>
      <td colspan="5">ИТОГО ПО ОТЧЁТУ (общее количество смен: ${rep.totalShifts}):</td>
      <td colspan="2">${rep.totalHours.toFixed(2)} ч.</td>
    </tr>
  `;
}

function exportCurrentReport() {
  if (!lastGeneratedReport) return;

  const fmt = document.getElementById("rep-export-format").value;
  const rep = lastGeneratedReport;

  if (fmt === "pdf") {
    showToast("Подготовка PDF-документа к печати/сохранению...", "success");
    window.print();
    return;
  }

  let content = "";
  let mime = "text/plain;charset=utf-8";
  let ext = fmt;

  if (fmt === "csv" || fmt === "xlsx") {
    // BOM + разделитель точка с запятой для корректного открытия кириллицы в MS Excel / LibreOffice Calc
    const sep = ";";
    const lines = [
      `Наименование отчета${sep}${rep.type}`,
      `Отчетный период${sep}${rep.period}`,
      `Дата формирования${sep}${rep.created_at}`,
      `Выборка${sep}${rep.filter}`,
      "",
      ["Сотрудник", "Должность и отдел", "Дата смены", "Начало", "Окончание", "Часы", "Выполненные работы"].join(sep)
    ];

    rep.rows.forEach(r => {
      lines.push(
        [
          `"${r.employee_name}"`,
          `"${r.position}"`,
          r.shift_date,
          r.time_start,
          r.time_end,
          String(r.hours.toFixed(2)).replace(".", ","),
          `"${r.works_text.replace(/"/g, '""')}"`
        ].join(sep)
      );
    });

    lines.push("");
    lines.push(`Итого смен${sep}${rep.totalShifts}`);
    lines.push(`Суммарное время (ч)${sep}${String(rep.totalHours.toFixed(2)).replace(".", ",")}`);

    content = "\uFEFF" + lines.join("\r\n");
    mime = "text/csv;charset=utf-8";
    ext = fmt === "xlsx" ? "csv" : "csv";
  } else {
    // Формат TXT (аналогично TxtExporter в src/export.py)
    const lines = [
      `=== ${rep.type.toUpperCase()} ===`,
      `ID отчёта: ${rep.id}`,
      `Дата формирования: ${rep.created_at}`,
      `Отчётный период: ${rep.period}`,
      `Фильтр сотрудников: ${rep.filter}`,
      "------------------------------------------------------------"
    ];
    rep.rows.forEach(r => {
      lines.push(
        `${r.shift_date} | ${r.employee_name} | ${r.time_start}-${r.time_end} (${r.hours.toFixed(2)} ч.) | Работы: ${r.works_text}`
      );
    });
    lines.push("------------------------------------------------------------");
    lines.push(`Итого смен: ${rep.totalShifts} | Суммарно часов: ${rep.totalHours.toFixed(2)}`);
    content = lines.join("\n");
  }

  const filename = `PAWS_${rep.id}_${rep.period.replace(/[^0-9-]/g, "_")}.${ext}`;
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);

  if (state.reportsHistory[0]) {
    state.reportsHistory[0].format = fmt.toUpperCase();
    saveState();
    renderReportHistory();
  }

  showToast(`Файл отчёта «${filename}» успешно создан и сохранён`, "success");
}

function renderReportHistory() {
  const tbody = document.getElementById("report-history-body");
  tbody.innerHTML = "";

  if (state.reportsHistory.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7">Сформированных отчётов пока нет.</td></tr>';
    return;
  }

  state.reportsHistory.forEach(item => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${item.id}</code></td>
      <td>${item.type}</td>
      <td>${item.period}</td>
      <td>${item.filter}</td>
      <td>${item.created_at}</td>
      <td>${item.author}</td>
      <td><span class="role-badge">${item.format}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// ================= 6. АДМИНИСТРИРОВАНИЕ (ТЗ п. 4.3, 4.4, 5.2 п.5) =================
function renderUsersTable() {
  const tbody = document.getElementById("users-table-body");
  tbody.innerHTML = "";

  state.users.forEach(u => {
    const emp = getEmployeeById(u.employee_id);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${u.username}</strong></td>
      <td>${emp ? `${emp.full_name} (<code>${emp.id}</code>)` : u.employee_id}</td>
      <td><span class="role-badge">${getRoleLabel(u.role)}</span></td>
      <td><code>${u.password_hash}</code> <span class="status-pill status-active">Скрыт</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function initAdminSection() {
  const userForm = document.getElementById("user-form");

  userForm.addEventListener("submit", e => {
    e.preventDefault();
    clearFormErrors(userForm);

    const username = document.getElementById("usr-username").value.trim();
    const password = document.getElementById("usr-password").value;
    const empId = document.getElementById("usr-emp").value;
    const role = document.getElementById("usr-role").value;

    let hasErr = false;
    if (!username) {
      setFieldError("fg-usr-username", "err-usr-username", "Укажите логин пользователя");
      hasErr = true;
    } else if (state.users.some(u => u.username.toLowerCase() === username.toLowerCase())) {
      setFieldError("fg-usr-username", "err-usr-username", "Пользователь с таким логином уже существует");
      hasErr = true;
    }

    if (!password || password.length < 6) {
      setFieldError("fg-usr-password", "err-usr-password", "Пароль должен содержать не менее 6 символов");
      hasErr = true;
    }

    if (hasErr) return;

    const pseudoHash = `pbkdf2_sha256$260000$${btoa(username + password).slice(0, 12)}...`;
    state.users.push({
      username,
      password_plain_demo: password,
      password_hash: pseudoHash,
      employee_id: empId,
      role
    });

    saveState();
    userForm.reset();
    renderUsersTable();
    showToast(`Учётная запись «${username}» создана`, "success");
  });

  // Сохранение системных настроек
  document.getElementById("settings-form").addEventListener("submit", e => {
    e.preventDefault();
    state.settings.orgName = document.getElementById("set-org-name").value.trim();
    state.settings.defaultFormat = document.getElementById("set-default-format").value;
    state.settings.maxShiftHours = Number(document.getElementById("set-max-shift-hours").value) || 24;
    state.settings.updatedAt = new Date().toISOString().slice(0, 16).replace("T", " ");

    document.getElementById("rep-export-format").value = state.settings.defaultFormat;
    document.getElementById("settings-updated-meta").textContent = `Последнее обновление настроек: ${state.settings.updatedAt}`;
    saveState();
    showToast("Системные параметры успешно сохранены", "success");
  });

  // Резервное копирование БД в JSON (ТЗ п. 4.3, 6.2)
  document.getElementById("btn-backup-export").addEventListener("click", () => {
    const dump = JSON.stringify(state, null, 2);
    const blob = new Blob([dump], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `PAWS_backup_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast("Резервная копия базы данных успешно сохранена", "success");
  });

  document.getElementById("backup-file-input").addEventListener("change", e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        const parsed = JSON.parse(ev.target.result);
        if (!parsed.employees || !parsed.shifts || !parsed.users) {
          throw new Error("Некорректная структура файла резервной копии");
        }
        state = parsed;
        saveState();
        populateSelectControls();
        renderAllSections();
        showToast("Данные успешно восстановлены из резервной копии", "success");
      } catch (err) {
        showToast("Ошибка восстановления: файл повреждён или имеет неверный формат", "error");
      }
    };
    reader.readAsText(file);
  });
}

// ================= МОДАЛЬНОЕ ОКНО ПОДТВЕРЖДЕНИЯ (ТЗ п. 4.5) =================
function openConfirmModal(message, onConfirm) {
  document.getElementById("modal-message").textContent = message;
  document.getElementById("confirm-modal").hidden = false;
  pendingConfirmAction = onConfirm;
}

function initModalAndReset() {
  document.getElementById("btn-modal-cancel").addEventListener("click", () => {
    document.getElementById("confirm-modal").hidden = true;
    pendingConfirmAction = null;
  });

  document.getElementById("btn-modal-confirm").addEventListener("click", () => {
    document.getElementById("confirm-modal").hidden = true;
    if (typeof pendingConfirmAction === "function") {
      pendingConfirmAction();
    }
    pendingConfirmAction = null;
  });

  document.getElementById("btn-reset-demo").addEventListener("click", () => {
    localStorage.removeItem(STORAGE_KEY);
    state = getInitialDemoData();
    if (currentUser) {
      populateSelectControls();
      renderAllSections();
    }
    showToast("Демонстрационные данные сброшены к начальному состоянию", "success");
  });
}

function renderAllSections() {
  renderDashboard();
  renderEmployees();
  renderShifts();
  renderSearchResults();
  renderReportHistory();
  renderUsersTable();
}

// Инициализация приложения
document.addEventListener("DOMContentLoaded", () => {
  initAuth();
  initNavigation();
  initEmployeesSection();
  initShiftsSection();
  initSearchSection();
  initReportsSection();
  initAdminSection();
  initModalAndReset();
});