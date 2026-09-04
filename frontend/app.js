const API_BASE = (() => {
  const configuredUrl = window.SEARCH_PORTAL_CONFIG?.apiBaseUrl?.trim();
  if (configuredUrl) return configuredUrl.replace(/\/$/, "");
  return window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
})();
const CONFIG = window.SEARCH_PORTAL_CONFIG || {};
const USE_UNICO_DIRECT = CONFIG.mode === "unico-direct";
const UNICO_DIRECT = CONFIG.unico || {};

const state = {
  columns: [],
  rows: [],
  filteredRows: [],
  selecting: false,
  startCell: null,
  selectionMode: "cells",
  lastPointer: null,
  selectionFrame: null,
  selectionMoveHandler: null,
};

const els = {
  menuButton: document.getElementById("menu-button"),
  topNav: document.getElementById("top-nav"),
  unicoConnection: document.getElementById("unico-connection"),
  unicoConnectionText: document.getElementById("unico-connection-text"),
  configWarning: document.getElementById("config-warning"),
  form: document.getElementById("unico-form"),
  input: document.getElementById("search-input"),
  inputCount: document.getElementById("input-count"),
  credential: document.getElementById("credential-input"),
  toggleCredential: document.getElementById("toggle-credential"),
  periodRange: document.getElementById("days-range"),
  periodValue: document.getElementById("days-value"),
  clearQuery: document.getElementById("clear-query"),
  searchButton: document.getElementById("search-button"),
  typeFilter: document.getElementById("type-filter"),
  resultFilter: document.getElementById("result-filter"),
  statusFilter: document.getElementById("status-filter"),
  copyTable: document.getElementById("copy-table"),
  message: document.getElementById("query-message"),
  emptyState: document.getElementById("empty-state"),
  tableContainer: document.getElementById("table-container"),
  resultCaption: document.getElementById("result-caption"),
  metricFound: document.getElementById("metric-found"),
  metricMissing: document.getElementById("metric-missing"),
  metricOccurrences: document.getElementById("metric-occurrences"),
  metricArchived: document.getElementById("metric-archived"),
  metricAnalysis: document.getElementById("metric-analysis"),
  metricPending: document.getElementById("metric-pending"),
  metricNotStarted: document.getElementById("metric-not-started"),
  metricNoRecent: document.getElementById("metric-no-recent"),
  toast: document.getElementById("toast"),
};

function initializeIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function route() {
  const pathRoute = location.pathname.split("/").filter(Boolean).pop();
  const requested = location.hash.replace("#/", "") || pathRoute || "unico";
  const routeName = ["documentacao", "unico"].includes(requested)
    ? requested
    : "unico";

  document.querySelectorAll("[data-route]").forEach((page) => {
    page.hidden = page.dataset.route !== routeName;
  });
  document.querySelectorAll("[data-route-link]").forEach((link) => {
    link.classList.toggle("active", link.dataset.routeLink === routeName);
  });

  els.topNav.classList.remove("open");
  window.scrollTo({ top: 0, behavior: "auto" });
}

function parseEntries(value) {
  return value
    .split(/[\r\n,;]+/)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeCpf(value) {
  const digits = String(value || "").replace(/\D/g, "");
  if (!digits || digits.length < 9 || digits.length > 11) return "";
  return digits.padStart(11, "0");
}

function detectEntry(entry) {
  if (entry.includes("@")) {
    return { raw: entry, type: "email", key: entry.trim().toLowerCase() };
  }

  const cpf = normalizeCpf(entry);
  if (cpf) return { raw: entry, type: "cpf", key: cpf };

  return { raw: entry, type: "nome", key: normalizeText(entry) };
}

function parseTerms(entries) {
  return entries
    .map(detectEntry)
    .filter((term) => term.key);
}

function updateInputCount() {
  const count = parseEntries(els.input.value).length;
  els.inputCount.textContent = `${count.toLocaleString("pt-BR")} de 2.000`;
  els.inputCount.style.color = count > 2000 ? "var(--red)" : "";
}

function updatePeriodLabel() {
  const days = Number(els.periodRange.value);
  const label = `${days.toLocaleString("pt-BR")} dias`;
  els.periodValue.textContent = label;
  els.periodRange.setAttribute("aria-valuetext", label);
}

function setLoading(loading) {
  els.searchButton.disabled = loading;
  els.searchButton.classList.toggle("is-loading", loading);
  els.searchButton.querySelector("span:not(.button-loader)").textContent =
    loading ? "Consultando" : "Consultar";
}

function showMessage(text, type = "error") {
  els.message.textContent = text;
  els.message.className = `message ${type}`;
  els.message.hidden = false;
}

function hideMessage() {
  els.message.hidden = true;
  els.message.textContent = "";
}

async function readErrorMessage(response) {
  const fallback = `Não foi possível concluir a consulta. Status HTTP: ${response.status}.`;
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) return `${fallback} Verifique os dados enviados.`;
    if (typeof payload.message === "string") return payload.message;
    return fallback;
  } catch {
    return fallback;
  }
}

function showToast(text) {
  els.toast.textContent = text;
  els.toast.hidden = false;
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    els.toast.hidden = true;
  }, 1800);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

function tsvValue(value) {
  return String(value ?? "").replaceAll("\t", " ").replaceAll(/\r?\n/g, " ");
}

function renderCell(column, value, rowIndex, columnIndex) {
  const safeValue = escapeHtml(value);
  const copyValue = escapeAttribute(tsvValue(value));
  if (column === "Status" && value) {
    return `
      <td tabindex="0" data-row="${rowIndex}" data-column="${columnIndex}" data-copy="${copyValue}">
        <span class="status-chip" data-status="${safeValue}">${safeValue}</span>
      </td>
    `;
  }
  return `<td tabindex="0" data-row="${rowIndex}" data-column="${columnIndex}" data-copy="${copyValue}">${safeValue}</td>`;
}

function updateMetrics(payload = null) {
  const total = payload?.total_consultado ?? 0;
  const found = payload?.total_encontrado ?? 0;
  const statusCount = (status) => state.rows.filter((row) => row.Status === status).length;

  els.metricFound.textContent = found.toLocaleString("pt-BR");
  els.metricMissing.textContent = Math.max(total - found, 0).toLocaleString("pt-BR");
  els.metricOccurrences.textContent = (payload?.total_ocorrencias ?? 0).toLocaleString("pt-BR");
  els.metricArchived.textContent = statusCount("Arquivado").toLocaleString("pt-BR");
  els.metricAnalysis.textContent = statusCount("Mesa de análise").toLocaleString("pt-BR");
  els.metricPending.textContent = statusCount("Pendente").toLocaleString("pt-BR");
  els.metricNotStarted.textContent = statusCount("Não iniciado").toLocaleString("pt-BR");
  els.metricNoRecent.textContent = statusCount("Sem acesso recente").toLocaleString("pt-BR");
  els.resultCaption.textContent = total
    ? `${state.rows.length.toLocaleString("pt-BR")} linha(s) retornada(s)`
    : "Aguardando consulta";
}

function applyFilters() {
  const type = els.typeFilter.value;
  const result = els.resultFilter.value;
  const status = els.statusFilter.value;

  state.filteredRows = state.rows.filter((row) => {
    const matchesType = type === "all" || row.Tipo === type;
    const matchesResult = result === "all" || row.Resultado === result;
    const matchesStatus = status === "all" || row.Status === status;
    return matchesType && matchesResult && matchesStatus;
  });
  renderTable();
}

function renderTable() {
  if (!state.columns.length) {
    els.emptyState.hidden = false;
    els.tableContainer.hidden = true;
    els.copyTable.disabled = true;
    return;
  }

  els.emptyState.hidden = true;
  els.tableContainer.hidden = false;
  els.copyTable.disabled = state.filteredRows.length === 0;

  if (!state.filteredRows.length) {
    els.tableContainer.innerHTML = `
      <div class="results-empty">
        <h3>Nenhum resultado para estes filtros</h3>
        <p>Altere o tipo, resultado ou status para visualizar outras linhas.</p>
      </div>
    `;
    return;
  }

  els.tableContainer.innerHTML = `
    <table class="results-table" id="results-table" aria-label="Resultados da consulta UNICO">
      <thead>
        <tr>${state.columns.map((column, columnIndex) => `
          <th tabindex="0" data-column="${columnIndex}" title="Selecionar coluna ${escapeAttribute(column)}">
            ${escapeHtml(column)}
          </th>
        `).join("")}</tr>
      </thead>
      <tbody>
        ${state.filteredRows.map((row, rowIndex) => `
          <tr>
            ${state.columns
              .map((column, columnIndex) => renderCell(column, row[column], rowIndex, columnIndex))
              .join("")}
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
  bindCellSelection();
}

function selectionTsv() {
  const table = document.getElementById("results-table");
  if (!table) return "";
  const selected = [...table.querySelectorAll("td.selected")];
  if (!selected.length) return "";
  const selectedHeaders = [...table.querySelectorAll("th.selected")];

  const rows = selected.map((cell) => Number(cell.dataset.row));
  const columns = selected.map((cell) => Number(cell.dataset.column));
  const bounds = {
    minRow: Math.min(...rows),
    maxRow: Math.max(...rows),
    minColumn: Math.min(...columns),
    maxColumn: Math.max(...columns),
  };

  const output = [];
  if (selectedHeaders.length) {
    output.push(
      state.columns
        .slice(bounds.minColumn, bounds.maxColumn + 1)
        .map(tsvValue)
        .join("\t")
    );
  }
  for (let row = bounds.minRow; row <= bounds.maxRow; row += 1) {
    const values = [];
    for (let column = bounds.minColumn; column <= bounds.maxColumn; column += 1) {
      const cell = table.querySelector(`td[data-row="${row}"][data-column="${column}"]`);
      values.push(cell?.dataset.copy ?? "");
    }
    output.push(values.join("\t"));
  }
  return output.join("\n");
}

function fullTableTsv() {
  const rows = [state.columns.map(tsvValue).join("\t")];
  state.filteredRows.forEach((row) => {
    rows.push(state.columns.map((column) => tsvValue(row[column])).join("\t"));
  });
  return rows.join("\n");
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const helper = document.createElement("textarea");
    helper.value = text;
    helper.style.position = "fixed";
    helper.style.opacity = "0";
    document.body.appendChild(helper);
    helper.select();
    document.execCommand("copy");
    helper.remove();
  }
}

function parseDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) || date.getFullYear() <= 1900 ? null : date;
}

function formatDate(value) {
  const date = parseDate(value);
  return date ? date.toLocaleDateString("pt-BR") : "";
}

function referenceDate(admission) {
  return parseDate(admission?.limitDate);
}

function isRecent(admission, days) {
  const date = referenceDate(admission);
  if (!date) return true;
  return date.getTime() >= Date.now() - days * 24 * 60 * 60 * 1000;
}

function admissionStatus(admission) {
  const overview = admission?.status?.overview || {};
  const rawCode = overview.code
    ?? overview.status
    ?? overview.status_overview
    ?? overview.statusOverview
    ?? admission?.status_overview
    ?? admission?.statusOverview
    ?? admission?.status?.code
    ?? admission?.status?.status
    ?? admission?.statusCode
    ?? admission?.status_code
    ?? admission?.status;
  const code = String(rawCode || "").toLowerCase().trim();

  if (code === "archived") return "Arquivado";
  if (code === "completed") return "Mesa de análise";
  if (code === "pending") return "Pendente";
  return "Não iniciado";
}

function isNotStarted(admission) {
  return !(admission?.documentList || []).some((document) =>
    [200, 220].includes(Number(document?.code))
  );
}

function bestAdmission(admissions) {
  const priority = {
    "Arquivado": 1,
    "Mesa de análise": 2,
    Pendente: 3,
    "Não iniciado": 4,
    "Sem acesso recente": 5,
  };
  return [...admissions].sort(
    (a, b) => (priority[admissionStatus(a)] || 999) - (priority[admissionStatus(b)] || 999)
  )[0] || null;
}

function documentName(document) {
  const tracked = {
    rg: "RG",
    cpf: "CPF",
    escolaridade: "Comprovante de escolaridade",
    "declaracao-de-escolaridade": "Autodeclaração de escolaridade",
    endereco: "Comprovante de endereço",
    "declaracao-de-endereco": "Autodeclaração de endereço",
    cracha: "Foto do crachá",
    nascimento: "Certidão de nascimento",
    casamento: "Certidão de casamento",
    dependentes: "Dependentes",
    divorcio: "Certidão de divórcio",
    beneficios: "Benefícios",
    pis: "PIS",
    exame: "Exame admissional",
    "info-pessoal": "Informações pessoais",
  };
  const slug = normalizeText(document?.slug).replaceAll(" ", "-");
  if (tracked[slug]) return tracked[slug];

  const title = document?.title || {};
  const value = typeof title === "object"
    ? title.pt_BR || title["pt-br"] || title.pt || ""
    : title;
  const normalized = normalizeText(value);
  return Object.values(tracked).find((name) => normalizeText(name) === normalized) || "";
}

function pendingDocuments(admission) {
  const pending = [];
  (admission?.documentList || []).forEach((document) => {
    const name = documentName(document);
    if (!name) return;
    if (![200, 220].includes(Number(document.code))) pending.push(name);
  });
  return [...new Set(pending)].join("; ");
}

function pendencies(status, admission) {
  if (status === "Arquivado") return "";
  if (status === "Mesa de análise") return "";
  if (status === "Não iniciado") return "Todos os documentos";
  if (status === "Pendente") return pendingDocuments(admission) || "Pendências";
  return "";
}

function authorizationValue(credential) {
  const trimmed = credential.trim();
  if (!trimmed) return "";
  return trimmed.includes(" ") ? trimmed : `Bearer ${trimmed}`;
}

function unicoColumns() {
  return [
    "Consulta",
    "Tipo",
    "Resultado",
    "Nome",
    "CPF",
    "Email",
    "Status",
    "Pendências",
    "Data limite",
    "Nº de ocorrências",
  ];
}

async function searchUnicoBackend(entries, credentialValue, days) {
  const response = await fetch(`${API_BASE}/unico/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tipo: "auto",
      entradas: entries,
      credencial: credentialValue,
      dias: days,
    }),
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return response.json();
}

async function searchUnicoDirect(entries, credential, days) {
  if (!UNICO_DIRECT.url || !UNICO_DIRECT.account || !UNICO_DIRECT.tenant) {
    throw new Error("Configuração direta da UNICO incompleta no arquivo config.js.");
  }

  const terms = parseTerms(entries);
  const rows = [];

  for (const [index, term] of terms.entries()) {
    const url = new URL(UNICO_DIRECT.url);
    url.searchParams.set("account", UNICO_DIRECT.account);
    url.searchParams.set("q", term.type === "nome" ? term.raw : term.key);

    let response;
    for (let attempt = 0; attempt < 4; attempt += 1) {
      try {
        response = await fetch(url.toString(), {
          method: "GET",
          headers: {
            authorization: authorizationValue(credential),
            tenant: UNICO_DIRECT.tenant,
            accept: "application/json",
          },
        });
      } catch {
        throw new Error(
          "O navegador não conseguiu acessar a UNICO diretamente. Se isso for bloqueio de CORS, a consulta precisa passar pelo backend interno."
        );
      }

      if (![500, 502, 503, 504].includes(response.status) || attempt === 3) break;
      await new Promise((resolve) => window.setTimeout(resolve, 1000 * 2 ** attempt));
    }

    if (response.status === 401 || response.status === 403) {
      throw new Error("Credencial não encontrada, tente novamente.");
    }
    if (response.status === 429) {
      throw new Error("A UNICO atingiu o limite de requisições. Aguarde alguns segundos e tente novamente.");
    }
    if ([500, 502, 503, 504].includes(response.status)) {
      throw new Error(
        `A UNICO apresentou uma instabilidade temporária (HTTP ${response.status}) mesmo após novas tentativas. Tente novamente em alguns instantes.`
      );
    }
    if (!response.ok) {
      throw new Error(`A UNICO respondeu com o código HTTP ${response.status}.`);
    }

    const payload = await response.json();
    const admissionsPayload = payload?.result?.admissions || {};
    const admissions = admissionsPayload.results || [];
    const total = Number(admissionsPayload.total || 0);

    if (!admissions.length) {
      rows.push({
        Consulta: term.raw,
        Tipo: term.type.toUpperCase(),
        Resultado: "Não encontrado",
        Nome: "",
        CPF: term.type === "cpf" ? term.key : "",
        Email: term.type === "email" ? term.key : "",
        Status: "",
        Pendências: "",
        "Data limite": "",
        "Nº de ocorrências": 0,
      });
    } else {
      const recent = admissions.filter((admission) => isRecent(admission, days));
      const admission = bestAdmission(recent.length ? recent : admissions);
      let status = recent.length ? admissionStatus(admission) : "Sem acesso recente";
      if (recent.length && status === "Pendente" && isNotStarted(admission)) {
        status = "Não iniciado";
      }
      const candidate = admission?.candidate || {};
      const identifier = candidate.identifier || {};

      rows.push({
        Consulta: term.raw,
        Tipo: term.type.toUpperCase(),
        Resultado: "Encontrado",
        Nome: candidate.name || "",
        CPF: identifier.value || (term.type === "cpf" ? term.key : ""),
        Email: candidate.email || "",
        Status: status,
        Pendências: pendencies(status, admission),
        "Data limite": formatDate(admission?.limitDate),
        "Nº de ocorrências": total,
      });
    }

    if (index < terms.length - 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 70));
    }
  }

  const found = rows.filter((row) => row.Resultado === "Encontrado").length;
  return {
    total_consultado: terms.length,
    total_encontrado: found,
    total_ocorrencias: rows.reduce((sum, row) => sum + Number(row["Nº de ocorrências"] || 0), 0),
    colunas: unicoColumns(),
    resultados: rows,
  };
}

function bindCellSelection() {
  const table = document.getElementById("results-table");
  if (!table) return;
  const scroller = els.tableContainer;

  function paintBounds(minRow, maxRow, minColumn, maxColumn, columnsOnly = false) {
    table.querySelectorAll("td").forEach((cell) => {
      const row = Number(cell.dataset.row);
      const column = Number(cell.dataset.column);
      cell.classList.toggle(
        "selected",
        row >= minRow && row <= maxRow && column >= minColumn && column <= maxColumn
      );
    });

    table.querySelectorAll("th[data-column]").forEach((header) => {
      const column = Number(header.dataset.column);
      header.classList.toggle(
        "selected",
        columnsOnly && column >= minColumn && column <= maxColumn
      );
    });
  }

  function paintSelection(endCell) {
    const startRow = Number(state.startCell.dataset.row);
    const startColumn = Number(state.startCell.dataset.column);
    const endRow = Number(endCell.dataset.row);
    const endColumn = Number(endCell.dataset.column);
    const minRow = Math.min(startRow, endRow);
    const maxRow = Math.max(startRow, endRow);
    const minColumn = Math.min(startColumn, endColumn);
    const maxColumn = Math.max(startColumn, endColumn);

    paintBounds(minRow, maxRow, minColumn, maxColumn);
  }

  function paintColumnSelection(endHeader) {
    const startColumn = Number(state.startCell.dataset.column);
    const endColumn = Number(endHeader.dataset.column);
    const minColumn = Math.min(startColumn, endColumn);
    const maxColumn = Math.max(startColumn, endColumn);
    paintBounds(0, state.filteredRows.length - 1, minColumn, maxColumn, true);
  }

  function updateSelectionFromPointer() {
    if (!state.selecting || !state.lastPointer) {
      state.selectionFrame = null;
      return;
    }

    const rect = scroller.getBoundingClientRect();
    const edge = 44;
    const maxSpeed = 22;
    const { clientX, clientY } = state.lastPointer;
    let deltaX = 0;
    let deltaY = 0;

    if (clientX < rect.left + edge) {
      deltaX = -maxSpeed * Math.min(1, (rect.left + edge - clientX) / edge);
    } else if (clientX > rect.right - edge) {
      deltaX = maxSpeed * Math.min(1, (clientX - (rect.right - edge)) / edge);
    }

    if (state.selectionMode === "cells") {
      if (clientY < rect.top + edge) {
        deltaY = -maxSpeed * Math.min(1, (rect.top + edge - clientY) / edge);
      } else if (clientY > rect.bottom - edge) {
        deltaY = maxSpeed * Math.min(1, (clientY - (rect.bottom - edge)) / edge);
      }
    }

    if (deltaX || deltaY) {
      scroller.scrollBy(deltaX, deltaY);
      const headerHeight = table.tHead?.offsetHeight || 0;
      const targetX = Math.max(rect.left + 2, Math.min(clientX, rect.left + scroller.clientWidth - 2));
      const targetTop = state.selectionMode === "columns" ? rect.top + 2 : rect.top + headerHeight + 2;
      const targetY = Math.max(
        targetTop,
        Math.min(clientY, rect.top + scroller.clientHeight - 2)
      );
      const selector = state.selectionMode === "columns" ? "th[data-column]" : "td";
      const target = document.elementFromPoint(targetX, targetY)?.closest(selector);
      if (target && table.contains(target)) {
        if (state.selectionMode === "columns") paintColumnSelection(target);
        else paintSelection(target);
      }
    }

    state.selectionFrame = window.requestAnimationFrame(updateSelectionFromPointer);
  }

  function startAutoScroll(event) {
    state.lastPointer = { clientX: event.clientX, clientY: event.clientY };
    if (!state.selectionFrame) {
      state.selectionFrame = window.requestAnimationFrame(updateSelectionFromPointer);
    }
  }

  table.addEventListener("pointerdown", (event) => {
    const header = event.target.closest("th[data-column]");
    const cell = event.target.closest("td");
    if (!cell && !header) return;
    event.preventDefault();
    state.selecting = true;
    state.startCell = header || cell;
    state.selectionMode = header ? "columns" : "cells";
    if (header) paintColumnSelection(header);
    else paintSelection(cell);
    startAutoScroll(event);
  });

  table.addEventListener("pointerover", (event) => {
    if (!state.selecting) return;
    const target = event.target.closest(
      state.selectionMode === "columns" ? "th[data-column]" : "td"
    );
    if (!target) return;
    if (state.selectionMode === "columns") paintColumnSelection(target);
    else paintSelection(target);
  });

  if (state.selectionMoveHandler) {
    window.removeEventListener("pointermove", state.selectionMoveHandler);
  }
  state.selectionMoveHandler = startAutoScroll;
  window.addEventListener("pointermove", state.selectionMoveHandler);
}

async function checkApi() {
  if (USE_UNICO_DIRECT) {
    const configured = Boolean(UNICO_DIRECT.url && UNICO_DIRECT.account && UNICO_DIRECT.tenant);
    els.unicoConnection.querySelector(".status-dot").className =
      `status-dot ${configured ? "online" : "offline"}`;
    els.unicoConnectionText.textContent = configured
      ? "Modo Grid configurado"
      : "Configuração pendente";
    els.configWarning.hidden = configured;
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/unico/config`);
    if (!response.ok) throw new Error();
    const config = await response.json();
    els.unicoConnection.querySelector(".status-dot").className =
      `status-dot ${config.configurada ? "online" : "offline"}`;
    els.unicoConnectionText.textContent = config.configurada
      ? "Integração configurada"
      : "Configuração pendente";
    els.configWarning.hidden = config.configurada;
  } catch {
    els.unicoConnection.querySelector(".status-dot").className = "status-dot offline";
    els.unicoConnectionText.textContent = API_BASE
      ? "Servidor indisponível"
      : "API não configurada";
    els.configWarning.hidden = false;
  }
}

async function submitSearch(event) {
  event.preventDefault();
  hideMessage();

  const entries = parseEntries(els.input.value);
  if (!entries.length) {
    showMessage("Adicione ao menos um CPF, nome ou e-mail.");
    els.input.focus();
    return;
  }
  if (entries.length > 2000) {
    showMessage("A consulta aceita no máximo 2.000 entradas por execução.");
    return;
  }
  if (!els.credential.value.trim()) {
    showMessage(
      "Para a requisição de busca, adicione a credencial. Caso tenha dúvida, abra a página de Documentação."
    );
    els.credential.focus();
    return;
  }

  setLoading(true);
  try {
    const days = Number(els.periodRange.value);
    const credentialValue = els.credential.value.trim();
    const payload = await searchUnicoBackend(entries, credentialValue, days);

    state.columns = payload.colunas;
    state.rows = payload.resultados;
    els.typeFilter.value = "all";
    els.resultFilter.value = "all";
    els.statusFilter.value = "all";
    updateMetrics(payload);
    applyFilters();
    showMessage(
      `${payload.total_encontrado} de ${payload.total_consultado} consulta(s) encontrada(s).`,
      "success"
    );
  } catch (error) {
    showMessage(error.message);
  } finally {
    setLoading(false);
  }
}

function clearQuery() {
  els.input.value = "";
  els.credential.value = "";
  els.credential.type = "password";
  els.toggleCredential.textContent = "Mostrar";
  state.columns = [];
  state.rows = [];
  state.filteredRows = [];
  els.typeFilter.value = "all";
  els.resultFilter.value = "all";
  els.statusFilter.value = "all";
  hideMessage();
  updateMetrics();
  updateInputCount();
  renderTable();
  els.input.focus();
}

window.addEventListener("hashchange", route);
window.addEventListener("pointerup", () => {
  state.selecting = false;
  state.lastPointer = null;
  if (state.selectionFrame) {
    window.cancelAnimationFrame(state.selectionFrame);
    state.selectionFrame = null;
  }
});
document.addEventListener("copy", (event) => {
  const text = selectionTsv();
  if (!text) return;
  event.preventDefault();
  event.clipboardData.setData("text/plain", text);
  showToast("Seleção copiada");
});

els.menuButton.addEventListener("click", () => {
  els.topNav.classList.toggle("open");
});
els.input.addEventListener("input", updateInputCount);
els.periodRange.addEventListener("input", updatePeriodLabel);
els.form.addEventListener("submit", submitSearch);
els.clearQuery.addEventListener("click", clearQuery);
els.typeFilter.addEventListener("change", applyFilters);
els.resultFilter.addEventListener("change", applyFilters);
els.statusFilter.addEventListener("change", applyFilters);
els.toggleCredential.addEventListener("click", () => {
  const visible = els.credential.type === "text";
  els.credential.type = visible ? "password" : "text";
  els.toggleCredential.textContent = visible ? "Mostrar" : "Ocultar";
});
els.copyTable.addEventListener("click", async () => {
  const selected = selectionTsv();
  await copyText(selected || fullTableTsv());
  showToast(selected ? "Seleção copiada" : "Tabela copiada");
});
document.querySelectorAll("[data-coming-soon]").forEach((button) => {
  button.addEventListener("click", () => {
    showToast(`${button.dataset.comingSoon}: em preparação`);
  });
});

initializeIcons();
route();
updateMetrics();
updateInputCount();
updatePeriodLabel();
renderTable();
checkApi();
