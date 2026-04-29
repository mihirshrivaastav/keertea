const formFields = [
  "productId", "name", "category", "pricePerUnit", "unit", "minWeight",
  "maxWeight", "inventoryGrams", "badge", "rating", "img", "desc", "isActive"
];

let adminProductsCache = [];

function getField(id) {
  return document.getElementById(id);
}

function getPayload() {
  return {
    name: getField("name").value.trim(),
    category: getField("category").value.trim(),
    pricePerUnit: Number(getField("pricePerUnit").value),
    unit: getField("unit").value,
    minWeight: Number(getField("minWeight").value),
    maxWeight: Number(getField("maxWeight").value),
    inventoryGrams: Number(getField("inventoryGrams").value),
    badge: getField("badge").value.trim(),
    rating: getField("rating").value.trim(),
    img: getField("img").value.trim(),
    desc: getField("desc").value.trim(),
    isActive: getField("isActive").value === "true"
  };
}

function resetForm() {
  formFields.forEach((id) => {
    getField(id).value = "";
  });
  getField("unit").value = "kg";
  getField("rating").value = "★★★★★";
  getField("isActive").value = "true";
  getField("imageFile").value = "";
  getField("uploadStatus").textContent = "No image uploaded yet.";
}

function fillForm(product) {
  getField("productId").value = product.id;
  getField("name").value = product.name;
  getField("category").value = product.category;
  getField("pricePerUnit").value = product.pricePerUnit;
  getField("unit").value = product.unit;
  getField("minWeight").value = product.minWeight;
  getField("maxWeight").value = product.maxWeight;
  getField("inventoryGrams").value = product.inventoryGrams;
  getField("badge").value = product.badge;
  getField("rating").value = product.rating;
  getField("img").value = product.img;
  getField("desc").value = product.desc;
  getField("isActive").value = String(product.isActive);
  getField("uploadStatus").textContent = product.img ? `Using image: ${product.img}` : "No image uploaded yet.";
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const text = await response.text();
  let data;

  try {
    data = text ? JSON.parse(text) : {};
  } catch (error) {
    // Keeping the first part of the raw response makes 500s much easier to spot from the UI.
    throw new Error(`Server returned an unexpected response instead of JSON. ${text.slice(0, 120)}`);
  }

  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}

async function loadProducts() {
  const products = await fetchJson("/api/admin/products");
  adminProductsCache = products;

  getField("productsList").innerHTML = products.map((product) => `
    <div class="card">
      <div class="card-top">
        <div>
          <h3>${product.name}</h3>
          <div class="muted">${product.category}</div>
        </div>
        <div class="price">Rs ${Math.round(product.pricePerUnit)}</div>
      </div>
      <p>${product.desc}</p>
      <div class="status">Inventory: ${product.inventoryGrams}g | Unit: ${product.unit} | Active: ${product.isActive ? "Yes" : "No"}</div>
      <div class="actions">
        <button class="secondary" data-edit-id="${product.id}">Edit</button>
        <button class="danger" data-delete-id="${product.id}">Delete</button>
      </div>
    </div>
  `).join("");
}

async function loadOrders() {
  const orders = await fetchJson("/api/admin/orders");
  const root = getField("ordersList");

  if (!orders.length) {
    root.innerHTML = "<div class='card'><p class='muted'>No orders yet.</p></div>";
    return;
  }

  root.innerHTML = orders.map((order) => `
    <div class="card">
      <div class="card-top">
        <div>
          <h3>Order #${order.id}</h3>
          <div class="muted">${order.customerName} | ${order.phone}</div>
        </div>
        <span class="pill">${order.paymentStatus}</span>
      </div>
      <div class="status">Placed: ${new Date(order.createdAt).toLocaleString()}</div>
      <div class="status">Payment: ${order.paymentMethod} (${order.paymentProvider})</div>
      <div class="status">Address: ${order.address}</div>
      <div class="order-items">
        ${order.items.map((item) => `
          <div>${item.productName} - ${item.selectedWeight}g x ${item.quantity} = Rs ${Math.round(item.lineTotal)}</div>
        `).join("")}
      </div>
      <div class="price" style="margin-top:8px;">Total: Rs ${Math.round(order.total)}</div>
    </div>
  `).join("");
}

async function saveProduct() {
  const payload = getPayload();
  const productId = getField("productId").value;
  const method = productId ? "PUT" : "POST";
  const url = productId ? `/api/admin/products/${productId}` : "/api/admin/products";

  await fetchJson(url, {
    method,
    body: JSON.stringify(payload)
  });

  resetForm();
  await Promise.all([loadProducts(), loadOrders()]);
}

async function uploadImage() {
  const fileInput = getField("imageFile");
  const file = fileInput.files[0];
  if (!file) {
    getField("uploadStatus").textContent = "Choose an image file first.";
    return;
  }

  const formData = new FormData();
  formData.append("image", file);

  const uploadBtn = getField("uploadBtn");
  uploadBtn.disabled = true;
  uploadBtn.textContent = "Uploading...";
  getField("uploadStatus").textContent = "Uploading image...";

  try {
    const response = await fetch("/api/admin/uploads", {
      method: "POST",
      body: formData
    });
    const text = await response.text();
    const data = text ? JSON.parse(text) : {};

    if (!response.ok) {
      throw new Error(data.error || "Upload failed");
    }

    getField("img").value = data.url;
    getField("uploadStatus").textContent = `Uploaded: ${data.filename}`;
  } catch (error) {
    getField("uploadStatus").textContent = error.message;
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = "Upload";
  }
}

async function removeProduct(id) {
  await fetchJson(`/api/admin/products/${id}`, { method: "DELETE" });
  await loadProducts();
}

function editProduct(productId) {
  const product = adminProductsCache.find((entry) => entry.id === productId);
  if (!product) {
    return;
  }

  fillForm(product);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function handleListActions(event) {
  const editButton = event.target.closest("[data-edit-id]");
  if (editButton) {
    editProduct(Number(editButton.dataset.editId));
    return;
  }

  const deleteButton = event.target.closest("[data-delete-id]");
  if (deleteButton) {
    removeProduct(Number(deleteButton.dataset.deleteId)).catch((error) => {
      alert(error.message);
    });
  }
}

async function initializeAdmin() {
  getField("saveBtn").addEventListener("click", () => {
    saveProduct().catch((error) => alert(error.message));
  });
  getField("resetBtn").addEventListener("click", resetForm);
  getField("uploadBtn").addEventListener("click", uploadImage);
  getField("productsList").addEventListener("click", handleListActions);

  resetForm();
  await Promise.all([loadProducts(), loadOrders()]);
}

document.addEventListener("DOMContentLoaded", () => {
  initializeAdmin().catch((error) => {
    alert(error.message);
  });
});
