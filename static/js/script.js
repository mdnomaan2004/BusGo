const $ = (id) => document.getElementById(id);
const state = { bus: null, date: "", selected: new Set(), price: 0 };
const money = (n) => "₹" + Number(n).toLocaleString("en-IN");
const esc = (s) => String(s).replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));

function toast(message) {
  const el = $("toast"); el.textContent = message; el.classList.add("show");
  clearTimeout(window.toastTimer); window.toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
}
function openModal(id) { $(id).classList.add("open"); $(id).setAttribute("aria-hidden", "false"); document.body.classList.add("modal-open"); }
function closeModal(id) {
  $(id).classList.remove("open"); $(id).setAttribute("aria-hidden", "true");
  if (!document.querySelector(".modal-backdrop.open")) document.body.classList.remove("modal-open");
}
document.querySelectorAll("[data-close]").forEach(b => b.addEventListener("click", () => closeModal(b.dataset.close)));
document.querySelectorAll(".modal-backdrop").forEach(backdrop => backdrop.addEventListener("click", e => { if (e.target === backdrop) closeModal(backdrop.id); }));
document.addEventListener("keydown", e => { if (e.key === "Escape") document.querySelectorAll(".modal-backdrop.open").forEach(m => closeModal(m.id)); });

$("mobileMenu").addEventListener("click", () => document.querySelector(".main-nav").classList.toggle("nav-open"));
$("swapCities").addEventListener("click", () => { const a=$("fromCity").value; $("fromCity").value=$("toCity").value; $("toCity").value=a; });

$("searchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const params = new URLSearchParams({from:$("fromCity").value,to:$("toCity").value,date:$("travelDate").value});
  if (params.get("from") === params.get("to")) return toast("Choose two different cities.");
  try {
    const response = await fetch("/api/buses?" + params);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Search failed.");
    renderBuses(data);
  } catch (err) { toast(err.message); }
});

function renderBuses(data) {
  $("resultsSection").hidden = false;
  $("resultsTitle").textContent = `${data.from} to ${data.to}`;
  $("resultsSubtitle").textContent = `Travel date: ${new Date(data.date+"T00:00:00").toLocaleDateString("en-IN",{day:"numeric",month:"long",year:"numeric"})}`;
  $("resultsCount").textContent = `${data.buses.length} buses`;
  $("noResults").hidden = data.buses.length !== 0;
  $("busList").innerHTML = data.buses.map(bus => `
    <article class="bus-card">
      <div class="bus-operator"><div class="operator-icon">B</div><div><h3>${esc(bus.operator)}</h3><p>${esc(bus.type)} · ★ ${bus.rating}</p></div></div>
      <div class="bus-time"><strong>${bus.departure}</strong><span>${esc(bus.from)}</span></div>
      <div class="duration"><span>──── ${esc(bus.duration)} ────</span><small>Direct journey</small></div>
      <div class="bus-time"><strong>${bus.arrival}</strong><span>${esc(bus.to)}</span></div>
      <div class="bus-price"><strong>${money(bus.price)}</strong><small>${bus.available_seats} seats left</small><button class="primary-button" data-book="${bus.id}" ${bus.available_seats===0?"disabled":""}>${bus.available_seats===0?"Sold out":"Select seats"}</button></div>
    </article>`).join("");
  $("busList").querySelectorAll("[data-book]").forEach(btn => btn.addEventListener("click", () => selectBus(Number(btn.dataset.book), data.date)));
  $("resultsSection").scrollIntoView({behavior:"smooth",block:"start"});
}

async function selectBus(id, journeyDate) {
  try {
    const response = await fetch(`/api/buses/${id}/seats?date=${encodeURIComponent(journeyDate)}`);
    const data = await response.json(); if (!response.ok) throw new Error(data.error);
    state.bus=data.bus; state.date=journeyDate; state.selected.clear(); state.price=data.bus.price;
    $("selectedBusInfo").textContent = `${data.bus.operator} · ${data.bus.from} → ${data.bus.to} · ${journeyDate}`;
    const booked = new Set(data.booked);
    $("seatGrid").innerHTML = data.seats.map((seat,i) => `<button type="button" class="seat ${booked.has(seat)?"booked":""}" data-seat="${seat}" ${booked.has(seat)?"disabled":""} aria-label="Seat ${seat}">${seat}</button>`).join("");
    $("seatGrid").querySelectorAll("[data-seat]").forEach(btn => btn.addEventListener("click", () => {
      const seat=btn.dataset.seat;
      if (state.selected.has(seat)) state.selected.delete(seat);
      else if (state.selected.size >= 6) return toast("You can select up to 6 seats.");
      else state.selected.add(seat);
      btn.classList.toggle("selected",state.selected.has(seat)); updateSeatSummary();
    }));
    updateSeatSummary(); openModal("seatModal");
  } catch(err) { toast(err.message || "Could not load seats."); }
}
function updateSeatSummary() {
  const seats=[...state.selected].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
  $("selectedSeatNames").textContent=seats.length?seats.join(", "):"No seats selected";
  $("seatTotal").textContent=money(seats.length*state.price);
  $("continueBooking").disabled=!seats.length;
}
$("continueBooking").addEventListener("click", () => {
  $("passengerTotal").textContent=`${state.selected.size} seat(s) · Total ${money(state.selected.size*state.price)}`;
  closeModal("seatModal"); openModal("passengerModal");
});
$("passengerForm").addEventListener("submit", async e => {
  e.preventDefault();
  const payload={bus_id:state.bus.id,date:state.date,name:$("passengerName").value.trim(),email:$("passengerEmail").value.trim(),phone:$("passengerPhone").value.trim(),seats:[...state.selected]};
  const button=e.submitter; button.disabled=true; button.textContent="Saving booking…";
  try {
    const response=await fetch("/api/bookings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const data=await response.json(); if(!response.ok) throw new Error(data.error || "Booking failed.");
    showTicket(data.booking); closeModal("passengerModal"); openModal("confirmationModal");
    $("passengerForm").reset();
  } catch(err) { toast(err.message); }
  finally { button.disabled=false; button.textContent="Confirm demo booking"; }
});
function showTicket(b) {
  $("ticketDetails").innerHTML=`
    <div class="ticket-ref"><span>BOOKING REFERENCE</span><strong>${esc(b.ref)}</strong></div>
    <div class="ticket-route"><div><small>FROM</small><strong>${esc(b.origin)}</strong><span>${esc(b.departure)}</span></div><div class="ticket-arrow">→</div><div><small>TO</small><strong>${esc(b.destination)}</strong><span>${esc(b.arrival)}</span></div></div>
    <div class="ticket-meta"><span>Passenger<strong>${esc(b.name)}</strong></span><span>Date<strong>${esc(b.date)}</strong></span><span>Seats<strong>${esc(b.seats.join(", "))}</strong></span><span>Total<strong>${money(b.total)}</strong></span></div>`;
}
$("doneButton").addEventListener("click",()=>{closeModal("confirmationModal");$("my-booking").scrollIntoView({behavior:"smooth"});});
$("lookupForm").addEventListener("submit",async e=>{
  e.preventDefault(); const ref=$("lookupCode").value.trim().toUpperCase();
  try {
    const response=await fetch(`/api/bookings/${encodeURIComponent(ref)}`); const data=await response.json();
    if(!response.ok) throw new Error(data.error);
    const b=data.booking;
    $("lookupResult").hidden=false;
    $("lookupResult").innerHTML=`<div class="lookup-top"><strong>Booking ${esc(b.booking_ref)}</strong><span class="status-pill">${esc(b.status)}</span></div><p><strong>${esc(b.origin)} → ${esc(b.destination)}</strong> · ${esc(b.journey_date)}</p><p>${esc(b.operator)} · Seats: ${esc(b.seats.join(", "))}</p><p>Passenger: ${esc(b.passenger_name)} · Total: <strong>${money(b.total)}</strong></p>`;
    $("lookupResult").scrollIntoView({behavior:"smooth",block:"center"});
  } catch(err) { $("lookupResult").hidden=true; toast(err.message); }
});
