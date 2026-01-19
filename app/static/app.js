const api = async (path, options = {}) => {
    const opts = {
        headers: { "Content-Type": "application/json" },
        ...options,
    };
    if (opts.body && typeof opts.body !== "string") {
        opts.body = JSON.stringify(opts.body);
    }

    const res = await fetch(path, opts);
    if (!res.ok) {
        let detail = await res.text();
        try { detail = JSON.parse(detail).detail || detail; } catch (_) {}
        throw new Error(detail || `Request failed (${res.status})`);
    }
    const text = await res.text();
    if (!text) return null;
    try { return JSON.parse(text); } catch (_) { return text; }
};

const toastEl = document.getElementById("toast");
function toast(message, isError = false) {
    toastEl.textContent = message;
    toastEl.classList.toggle("error", isError);
    toastEl.classList.add("show");
    toastEl.classList.remove("hidden");
    setTimeout(() => toastEl.classList.remove("show"), 2600);
}

async function refreshWeight() {
    try {
        const data = await api("/api/weight/live");
        const value = data.weight_kg != null ? data.weight_kg.toFixed(2) : "--.-";
        document.getElementById("live-weight").textContent = value;
        document.getElementById("weight-meta").textContent = data.captured_at
            ? `Updated ${new Date(data.captured_at).toLocaleTimeString()} (${data.source})`
            : "Waiting for indicator…";
        document.getElementById("serial-status").textContent = data.connected
            ? `Serial: live (${data.source})`
            : `Serial: ${data.source}`;
    } catch (err) {
        console.error(err);
    }
}

async function loadSerialSettings() {
    try {
        const data = await api("/api/serial/settings");
        const form = document.getElementById("serial-form");
        form.port.value = data.port || "";
        form.baudrate.value = data.baudrate || 9600;
        form.bytesize.value = data.bytesize || 8;
        form.parity.value = data.parity || "N";
        form.stopbits.value = data.stopbits || 1;
        form.simulate.checked = data.simulate || false;
        document.getElementById("serial-status").textContent = data.connected
            ? `Serial: live (${data.port || data.simulate ? "simulated" : "unknown"})`
            : "Serial: idle";
    } catch (err) {
        toast(`Could not load serial config: ${err.message}`, true);
    }
}

async function connectSerial(event) {
    event.preventDefault();
    const form = document.getElementById("serial-form");
    const payload = {
        port: form.port.value || null,
        baudrate: Number(form.baudrate.value),
        bytesize: Number(form.bytesize.value),
        parity: form.parity.value,
        stopbits: Number(form.stopbits.value),
        simulate: form.simulate.checked,
    };
    try {
        await api("/api/serial/connect", { method: "POST", body: payload });
        toast("Serial connected");
        await loadSerialSettings();
    } catch (err) {
        toast(`Serial connect failed: ${err.message}`, true);
    }
}

async function disconnectSerial() {
    try {
        await api("/api/serial/disconnect", { method: "POST" });
        toast("Serial disconnected");
        await loadSerialSettings();
    } catch (err) {
        toast(`Disconnect failed: ${err.message}`, true);
    }
}

function formToPayload(form) {
    const data = new FormData(form);
    const payload = {};
    data.forEach((v, k) => payload[k] = v);
    return payload;
}

async function handleWeighIn(event) {
    event.preventDefault();
    const payload = formToPayload(event.target);
    payload.gross_kg = payload.gross_kg ? Number(payload.gross_kg) : null;
    try {
        const ticket = await api("/api/tickets/weigh-in", { method: "POST", body: payload });
        toast(`Gross captured for ticket ${ticket.id}`);
        event.target.reset();
        await loadTickets();
    } catch (err) {
        toast(err.message, true);
    }
}

async function handleWeighOut(event) {
    event.preventDefault();
    const payload = formToPayload(event.target);
    const id = Number(payload.ticket_id);
    if (!id) return toast("Ticket ID is required", true);
    const body = { tare_kg: payload.tare_kg ? Number(payload.tare_kg) : null };
    try {
        const ticket = await api(`/api/tickets/${id}/weigh-out`, { method: "POST", body });
        toast(`Tare captured for ticket ${ticket.id}`);
        await loadTickets();
    } catch (err) {
        toast(err.message, true);
    }
}

async function handleFinalize(event) {
    event.preventDefault();
    const payload = formToPayload(event.target);
    const id = Number(payload.ticket_id);
    if (!id) return toast("Ticket ID is required", true);
    const body = {
        qc_status: payload.qc_status || null,
        qc_note: payload.qc_note || null,
        remarks: payload.remarks || null,
    };
    try {
        const ticket = await api(`/api/tickets/${id}/finalize`, { method: "POST", body });
        toast(`Ticket ${ticket.ticket_no || ticket.id} finalized`);
        await loadTickets();
        await loadQueue();
    } catch (err) {
        toast(err.message, true);
    }
}

async function loadTickets() {
    try {
        const tickets = await api("/api/tickets?limit=60");
        const tbody = document.getElementById("ticket-table");
        if (!Array.isArray(tickets)) return;
        tbody.innerHTML = tickets.map(t => `
            <tr>
                <td>${t.id}</td>
                <td>${t.ticket_no || "—"}</td>
                <td>${t.vehicle_plate}</td>
                <td>${t.direction}</td>
                <td>${t.gross_kg?.toFixed(2) ?? "—"}</td>
                <td>${t.tare_kg?.toFixed(2) ?? "—"}</td>
                <td>${t.net_kg?.toFixed(2) ?? "—"}</td>
                <td><span class="status-badge ${t.status}">${t.status}</span></td>
                <td>${t.partner_name}</td>
                <td>${t.product_name}</td>
                <td>${new Date(t.updated_at).toLocaleString()}</td>
            </tr>
        `).join("");
    } catch (err) {
        console.error(err);
        toast("Could not load tickets", true);
    }
}

async function loadQueue() {
    try {
        const queue = await api("/api/sync/queue");
        document.getElementById("sync-status").textContent = `Sync queue: ${queue.length}`;
    } catch (err) {
        console.error(err);
    }
}

async function triggerSync() {
    try {
        await api("/api/sync/run", { method: "POST" });
        toast("Sync triggered");
        await loadQueue();
    } catch (err) {
        toast(`Sync failed: ${err.message}`, true);
    }
}

document.getElementById("weighin-form").addEventListener("submit", handleWeighIn);
document.getElementById("weighout-form").addEventListener("submit", handleWeighOut);
document.getElementById("finalize-form").addEventListener("submit", handleFinalize);
document.getElementById("serial-form").addEventListener("submit", connectSerial);
document.getElementById("connect-serial").addEventListener("click", connectSerial);
document.getElementById("disconnect-serial").addEventListener("click", disconnectSerial);
document.getElementById("refresh-tickets").addEventListener("click", loadTickets);
document.getElementById("sync-now").addEventListener("click", triggerSync);

loadSerialSettings();
loadTickets();
loadQueue();
refreshWeight();
setInterval(refreshWeight, 1000);
setInterval(loadQueue, 6000);
