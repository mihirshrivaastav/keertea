// Product data is now loaded from the Flask API instead of being hardcoded.
let PRODUCTS = [];

// Cart is stored as an object keyed by "productId-weight" so the same product
// can exist in multiple weight variants at the same time.
let cart = {};

// Stores the current slider selection for each product card before it is added.
const localWeights = {};
let toastTimer;

function formatCurrency(amount) {
  return `Rs ${Math.round(amount).toLocaleString()}`;
}

function findProduct(id) {
  return PRODUCTS.find((product) => product.id === id);
}

function computeItemPrice(product, weight) {
  if (product.unit === "kg") {
    return product.pricePerUnit * weight / 1000;
  }
  return product.pricePerUnit * weight / 100;
}

async function fetchProducts() {
  const response = await fetch("/api/products");
  if (!response.ok) {
    throw new Error("Unable to load products right now.");
  }
  PRODUCTS = await response.json();
}

// Builds the product grid from the latest catalog returned by the backend.
function buildProducts() {
  const grid = document.getElementById("productsGrid");

  if (!PRODUCTS.length) {
    grid.innerHTML = `
      <div class="product-card">
        <div class="product-body">
          <div class="product-name">No products available</div>
          <div class="product-desc">Please add products from the admin panel.</div>
        </div>
      </div>
    `;
    return;
  }

  grid.innerHTML = PRODUCTS.map((product) => {
    const initialWeight = product.minWeight;
    const priceDisplay = product.unit === "kg"
      ? `${formatCurrency(product.pricePerUnit)}/kg`
      : `${formatCurrency(product.pricePerUnit)}/${product.unit}`;
    const initialPrice = computeItemPrice(product, initialWeight);

    return `
      <div class="product-card" id="pc-${product.id}">
        <div class="product-img-wrap">
          <img src="${product.img}" alt="${product.name}" loading="lazy">
          <span class="product-badge">${product.badge}</span>
        </div>
        <div class="product-body">
          <div class="product-meta">
            <span class="product-category">${product.category}</span>
            <span class="product-rating">${product.rating}</span>
          </div>
          <div class="product-name">${product.name}</div>
          <div class="product-desc">${product.desc}</div>
          <div class="product-price-row">
            <span class="product-price" id="price-${product.id}">${formatCurrency(initialPrice)}</span>
            <span class="product-weight">${priceDisplay}</span>
          </div>
          <div class="qty-row">
            <div style="width:100%;display:flex;flex-direction:column;gap:.5rem">
              <label style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">Choose Weight</label>
              <div style="display:flex;align-items:center;gap:.6rem">
                <input
                  type="range"
                  id="weight-${product.id}"
                  min="${product.minWeight}"
                  max="${product.maxWeight}"
                  value="${initialWeight}"
                  step="50"
                  style="flex:1;cursor:pointer;"
                  oninput="updateWeight(${product.id})"
                >
                <span
                  class="product-weight"
                  id="weight-display-${product.id}"
                  style="background:transparent;min-width:60px;text-align:right;font-size:.85rem;font-weight:500"
                >${initialWeight}g</span>
              </div>
              <span class="product-desc" style="margin:0">In stock: ${product.inventoryGrams}g</span>
            </div>
          </div>
          <button class="add-to-cart" id="atc-${product.id}" onclick="addToCart(${product.id})">
            Add to Cart
          </button>
        </div>
      </div>
    `;
  }).join("");
}

function updateWeight(id) {
  const product = findProduct(id);
  const weight = parseInt(document.getElementById(`weight-${id}`).value, 10);
  localWeights[id] = weight;

  document.getElementById(`weight-display-${id}`).textContent = `${weight}g`;
  document.getElementById(`price-${id}`).textContent = formatCurrency(computeItemPrice(product, weight));
}

function addToCart(id) {
  const product = findProduct(id);
  const weight = localWeights[id] || product.minWeight;
  const cartKey = `${id}-${weight}`;

  if ((weight * ((cart[cartKey]?.qty || 0) + 1)) > product.inventoryGrams) {
    showToast(`Only ${product.inventoryGrams}g of ${product.name} is available.`);
    return;
  }

  if (cart[cartKey]) {
    cart[cartKey].qty += 1;
  } else {
    cart[cartKey] = {
      ...product,
      weight,
      price: computeItemPrice(product, weight),
      qty: 1,
    };
  }

  updateCartCount();
  renderCart();

  const btn = document.getElementById(`atc-${id}`);
  btn.textContent = "Added!";
  btn.classList.add("added");
  setTimeout(() => {
    btn.textContent = "Add to Cart";
    btn.classList.remove("added");
  }, 1600);

  showToast(`${product.name} (${weight}g) added to cart.`);

  const counter = document.getElementById("cartCount");
  counter.classList.remove("bump");
  void counter.offsetWidth;
  counter.classList.add("bump");
}

function updateCartCount() {
  const total = Object.values(cart).reduce((sum, item) => sum + item.qty, 0);
  document.getElementById("cartCount").textContent = total;
}

// Re-renders the drawer from source-of-truth cart state after every change.
function renderCart() {
  const wrap = document.getElementById("cartItems");
  const footer = document.getElementById("cartFooter");
  const items = Object.values(cart);

  if (!items.length) {
    wrap.innerHTML = `<div class="cart-empty"><div class="cart-empty-icon">Cart</div><p>Your cart is empty.<br>Add some natural goodness!</p></div>`;
    footer.style.display = "none";
    return;
  }

  const subtotal = items.reduce((sum, item) => sum + (item.price * item.qty), 0);
  wrap.innerHTML = items.map((item, idx) => `
    <div class="cart-item">
      <img class="cart-item-img" src="${item.img}" alt="${item.name}">
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-weight">${item.weight}g</div>
        <div class="cart-item-row">
          <span class="cart-item-price">${formatCurrency(item.price * item.qty)}</span>
          <div style="display:flex;align-items:center;gap:.2rem">
            <div class="cart-item-qty">
              <button class="cq-btn" onclick="updateCartQty(${idx}, -1)">-</button>
              <span class="cq-val">${item.qty}</span>
              <button class="cq-btn" onclick="updateCartQty(${idx}, 1)">+</button>
            </div>
            <button class="remove-btn" onclick="removeFromCart(${idx})">Remove</button>
          </div>
        </div>
      </div>
    </div>
  `).join("");

  document.getElementById("cartSubtotal").textContent = formatCurrency(subtotal);
  document.getElementById("cartTotal").textContent = formatCurrency(subtotal);
  footer.style.display = "block";
}

function updateCartQty(idx, delta) {
  const key = Object.keys(cart)[idx];
  if (!key) {
    return;
  }

  const nextQty = Math.max(1, cart[key].qty + delta);
  const available = cart[key].inventoryGrams;
  if ((cart[key].weight * nextQty) > available) {
    showToast(`Only ${available}g of ${cart[key].name} is available.`);
    return;
  }

  cart[key].qty = nextQty;
  updateCartCount();
  renderCart();
}

function removeFromCart(idx) {
  const key = Object.keys(cart)[idx];
  if (key) {
    delete cart[key];
  }
  updateCartCount();
  renderCart();
}

function toggleCart() {
  // Body scroll is locked only while the drawer is open.
  document.getElementById("cartOverlay").classList.toggle("open");
  document.getElementById("cartDrawer").classList.toggle("open");
  document.body.style.overflow = document.getElementById("cartDrawer").classList.contains("open") ? "hidden" : "";
  renderCart();
}

function openCheckout() {
  const items = Object.values(cart);
  if (!items.length) {
    showToast("Cart is empty.");
    return;
  }

  const subtotal = items.reduce((sum, item) => sum + (item.price * item.qty), 0);
  document.getElementById("checkoutSummary").innerHTML = `
    <h3>Order Summary</h3>
    ${items.map((item) => `
      <div class="ms-row">
        <span>${item.name} (${item.weight}g) x ${item.qty}</span>
        <span>${formatCurrency(item.price * item.qty)}</span>
      </div>
    `).join("")}
    <div class="ms-total"><span>Total</span><span>${formatCurrency(subtotal)}</span></div>
  `;
  document.getElementById("checkoutModal").classList.add("open");
  toggleCart();
  document.body.style.overflow = "hidden";
}

function closeCheckout() {
  document.getElementById("checkoutModal").classList.remove("open");
  document.body.style.overflow = "";
}

async function placeOrder() {
  // Basic front-end validation is followed by an API call that persists the order.
  const customerName = document.getElementById("chkName").value.trim();
  const phone = document.getElementById("chkPhone").value.trim();
  const address = document.getElementById("chkAddr").value.trim();
  const paymentMethod = document.getElementById("chkPay").value;
  if (!customerName || !phone || !address) {
    showToast("Please fill all fields.");
    return;
  }

  const payButton = document.querySelector(".pay-btn");
  payButton.disabled = true;
  payButton.textContent = "Processing...";

  try {
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customerName,
        phone,
        address,
        paymentMethod,
        items: Object.values(cart).map((item) => ({
          id: item.id,
          weight: item.weight,
          qty: item.qty,
        })),
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Unable to place order.");
    }

    closeCheckout();
    document.getElementById("successMsg").innerHTML = `
      Thank you, <strong>${customerName}</strong>.<br>
      Order #${data.order.id} has been created successfully.<br><br>
      Payment status: ${data.order.paymentStatus}<br>
      Reference: ${data.order.paymentReference || "Will be assigned at collection"}
    `;
    document.getElementById("successModal").classList.add("open");
    cart = {};
    updateCartCount();
    document.body.style.overflow = "hidden";

    await fetchProducts();
    buildProducts();
  } catch (error) {
    showToast(error.message);
  } finally {
    payButton.disabled = false;
    payButton.textContent = "Proceed to Payment";
  }
}

function closeSuccess() {
  document.getElementById("successModal").classList.remove("open");
  document.body.style.overflow = "";
}

function openMobile() {
  document.getElementById("mobileMenu").classList.add("open");
}

function closeMobile() {
  document.getElementById("mobileMenu").classList.remove("open");
}

// Reuses a single toast element so messages do not stack on screen.
function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}

window.addEventListener("scroll", () => {
  // Adds a shadow once the page has moved past the hero top edge.
  document.getElementById("navbar").classList.toggle("scrolled", window.scrollY > 40);
});

async function initializeStorefront() {
  try {
    await fetchProducts();
    buildProducts();
    updateCartCount();
    renderCart();
  } catch (error) {
    document.getElementById("productsGrid").innerHTML = `
      <div class="product-card">
        <div class="product-body">
          <div class="product-name">Store is temporarily unavailable</div>
          <div class="product-desc">${error.message}</div>
        </div>
      </div>
    `;
  }
}

// Initialize the storefront after the backend-backed catalog is available.
initializeStorefront();
