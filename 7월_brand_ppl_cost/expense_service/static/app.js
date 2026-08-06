let allBrands = [];
let topics = [];
const selected = new Map(); // db_name -> display_name

function el(tag, attrs = {}, children = []) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === "text") e.textContent = v;
    else e.setAttribute(k, v);
  });
  children.forEach(c => e.appendChild(c));
  return e;
}

async function loadDefaults() {
  const res = await fetch("/api/defaults");
  const data = await res.json();
  document.getElementById("startDate").value = data.start_date.slice(0, 10);
  document.getElementById("endDate").value = data.end_date.slice(0, 10);
  document.getElementById("label").value = data.start_date.slice(0, 7);
  data.buckets.forEach(addBucketRow);
  data.brands.forEach(b => selected.set(b.db_name, b.db_name));
}

async function loadCatalog() {
  const res = await fetch("/api/brand-catalog");
  const data = await res.json();
  allBrands = data.brands;
  topics = data.topics;
  const sel = document.getElementById("topicFilter");
  topics.forEach(t => sel.appendChild(el("option", { value: t, text: t })));
  renderBrandList();
  renderChips();
}

function renderBrandList() {
  const q = document.getElementById("brandSearch").value.trim().toLowerCase();
  const topicFilter = document.getElementById("topicFilter").value;
  const container = document.getElementById("brandList");
  container.innerHTML = "";

  const filtered = allBrands.filter(b => {
    if (topicFilter && b.topic !== topicFilter) return false;
    if (!q) return true;
    return (b.brand_name_kr || "").toLowerCase().includes(q) ||
           (b.brand_name_en || "").toLowerCase().includes(q);
  });

  let lastTopic = null;
  filtered.forEach(b => {
    if (b.topic !== lastTopic) {
      container.appendChild(el("div", { class: "brand-topic-header", text: b.topic }));
      lastTopic = b.topic;
    }
    const checked = selected.has(b.brand_name_kr);
    const label = el("label");
    const cb = el("input", { type: "checkbox" });
    cb.checked = checked;
    cb.addEventListener("change", () => {
      if (cb.checked) selected.set(b.brand_name_kr, b.brand_name_kr);
      else selected.delete(b.brand_name_kr);
      document.getElementById("selectedCount").textContent = selected.size;
      renderChips();
    });
    label.appendChild(cb);
    label.appendChild(document.createTextNode(" " + b.brand_name_kr));
    container.appendChild(label);
  });

  document.getElementById("selectedCount").textContent = selected.size;
}

function renderChips() {
  const box = document.getElementById("selectedChips");
  box.innerHTML = "";
  document.getElementById("selectedCount").textContent = selected.size;
  for (const [dbName] of selected.entries()) {
    const chip = el("span", { class: "chip" });
    const removeBtn = el("button", { text: "×" });
    removeBtn.addEventListener("click", () => {
      selected.delete(dbName);
      renderChips();
      renderBrandList();
    });
    chip.appendChild(document.createTextNode(dbName + " "));
    chip.appendChild(removeBtn);
    box.appendChild(chip);
  }
}

function addBucketRow(bucket) {
  bucket = bucket || {
    min: 10000, max: 100000, adjustment: 0.5,
    instagram: { feed: [100, 200], reel: [150, 400] },
    youtube: { ppl: [200, 300], shorts: [250, 300] },
  };
  const tbody = document.querySelector("#bucketTable tbody");
  const tr = el("tr");

  const rangeCell = el("td");
  const minInput = el("input", { type: "number", class: "range-input", value: bucket.min });
  const maxInput = el("input", { type: "number", class: "range-input", value: bucket.max });
  rangeCell.append(minInput, document.createTextNode(" ~ "), maxInput);

  const adjCell = el("td");
  const adjInput = el("input", { type: "number", class: "adj-input", step: "1", value: Math.round(bucket.adjustment * 100) });
  adjCell.append(adjInput, document.createTextNode("%"));

  function rangeInputs(pair) {
    const cell = el("td");
    const lo = el("input", { type: "number", value: pair[0] });
    const hi = el("input", { type: "number", value: pair[1] });
    cell.append(lo, document.createTextNode(" ~ "), hi);
    cell._get = () => [Number(lo.value), Number(hi.value)];
    return cell;
  }

  const feedCell = rangeInputs(bucket.instagram.feed);
  const reelCell = rangeInputs(bucket.instagram.reel);
  const pplCell = rangeInputs(bucket.youtube.ppl);
  const shortsCell = rangeInputs(bucket.youtube.shorts);

  const removeCell = el("td");
  const removeBtn = el("button", { text: "삭제" });
  removeBtn.addEventListener("click", () => tr.remove());
  removeCell.appendChild(removeBtn);

  tr.append(rangeCell, adjCell, feedCell, reelCell, pplCell, shortsCell, removeCell);
  tr._collect = () => ({
    min: Number(minInput.value),
    max: Number(maxInput.value),
    adjustment: Number(adjInput.value) / 100,
    instagram: { feed: feedCell._get(), reel: reelCell._get() },
    youtube: { ppl: pplCell._get(), shorts: shortsCell._get() },
  });
  tbody.appendChild(tr);
}

function collectBuckets() {
  return [...document.querySelectorAll("#bucketTable tbody tr")].map(tr => tr._collect());
}

async function generate() {
  const label = document.getElementById("label").value.trim();
  const startDate = document.getElementById("startDate").value;
  const endDate = document.getElementById("endDate").value;
  if (!startDate || !endDate) { alert("기간을 선택하세요."); return; }
  if (selected.size === 0) { alert("브랜드를 하나 이상 선택하세요."); return; }

  const payload = {
    label,
    start_date: startDate + " 00:00:00",
    end_date: endDate + " 00:00:00",
    brands: [...selected.entries()].map(([db_name, display_name]) => ({ db_name, display_name })),
    buckets: collectBuckets(),
  };

  const status = document.getElementById("status");
  const btn = document.getElementById("generateBtn");
  btn.disabled = true;
  status.textContent = "생성 중... (DB 조회 + 계산, 수 초~수십 초 걸릴 수 있어요)";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    renderResult(data);
    status.textContent = "완료!";
  } catch (e) {
    status.textContent = "실패: " + e.message;
  } finally {
    btn.disabled = false;
  }
}

function renderResult(data) {
  const card = document.getElementById("resultCard");
  card.hidden = false;

  const downloads = document.getElementById("downloads");
  downloads.innerHTML = "";
  const labels = {
    xlsx: "엑셀 리포트 (xlsx)",
    summary_csv: "브랜드별 요약 (csv)",
    brand_cost_csv: "brand_cost (raw csv)",
    brand_user_csv: "brand_user (raw csv)",
    brand_user_cost_csv: "brand_user_cost (csv)",
  };
  Object.entries(data.files).forEach(([key, filename]) => {
    const a = el("a", {
      href: `${data.download_base}/${encodeURIComponent(filename)}`,
      text: "⬇ " + (labels[key] || filename),
    });
    downloads.appendChild(a);
  });

  const table = document.getElementById("summaryTable");
  table.innerHTML = "";
  if (data.summary.length === 0) return;
  const headerRow = el("tr");
  Object.keys(data.summary[0]).forEach(k => headerRow.appendChild(el("th", { text: k })));
  table.appendChild(headerRow);
  data.summary.forEach(row => {
    const tr = el("tr");
    Object.values(row).forEach(v => tr.appendChild(el("td", { text: v })));
    table.appendChild(tr);
  });
}

document.getElementById("brandSearch").addEventListener("input", renderBrandList);
document.getElementById("topicFilter").addEventListener("change", renderBrandList);
document.getElementById("clearSelectionBtn").addEventListener("click", () => {
  selected.clear();
  renderBrandList();
  renderChips();
});
document.getElementById("addBucketBtn").addEventListener("click", () => addBucketRow());
document.getElementById("generateBtn").addEventListener("click", generate);

(async function init() {
  await loadDefaults();
  await loadCatalog();
})();
