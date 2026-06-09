import { useEffect, useMemo, useState } from "react";

import { apiGet, apiPatch, apiPost } from "../api/client";
import Navbar from "../components/Navbar";
import useCurrentOperator from "../hooks/useCurrentOperator";

function ProductsPage() {
  const { authLoading, authError } = useCurrentOperator();

  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [quantities, setQuantities] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadData() {
    try {
      const productsData = await apiGet("/api/v1/products");
      const cartData = await apiGet("/cart");

      setProducts(productsData);
      setCart(cartData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && !authError) {
      loadData();
    }
  }, [authLoading, authError]);

  const cartItemsByProductId = useMemo(() => {
    const map = new Map();

    if (!cart) {
      return map;
    }

    for (const item of cart.items) {
      map.set(item.product.id, item);
    }

    return map;
  }, [cart]);

  const categories = useMemo(() => {
    return [...new Set(products.map((product) => product.category.name))];
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      if (selectedCategory === "ALL") {
        return true;
      }

      return product.category.name === selectedCategory;
    });
  }, [products, selectedCategory]);

  function getQuantityForProduct(productId) {
    const value = quantities[productId];
    return value && value > 0 ? value : 1;
  }

  function handleQuantityChange(productId, value) {
    const parsed = Number(value);

    setQuantities({
      ...quantities,
      [productId]: parsed > 0 ? parsed : 1,
    });
  }

  async function handleAddToCart(product) {
    setError("");

    const quantityToAdd = getQuantityForProduct(product.id);
    const cartItem = cartItemsByProductId.get(product.id);

    try {
      if (cartItem) {
        const newQuantity = cartItem.quantity + quantityToAdd;

        await apiPatch(`/cart/items/${cartItem.id}`, {
          quantity: newQuantity,
        });
      } else {
        await apiPost("/cart/items", {
          product_id: product.id,
          quantity: quantityToAdd,
        });
      }

      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  if (authLoading) {
    return (
      <main className="page">
        <section className="card">
          <p>Sprawdzanie sesji...</p>
        </section>
      </main>
    );
  }

  if (authError) {
    return null;
  }

  return (
    <>
      <Navbar />

      <main className="products-layout">
        <aside className="filters-panel">
          <h2>Filtry</h2>

          <label>
            Kategoria
            <select
              value={selectedCategory}
              onChange={(event) => setSelectedCategory(event.target.value)}
            >
              <option value="ALL">Wszystkie</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>
        </aside>

        <section className="products-content">
          <h1>Lista produktów</h1>

          {loading && <p>Ładowanie produktów...</p>}
          {error && <p className="error">{error}</p>}

          {!loading && !error && (
            <>
              <p>
                Wyświetlono: {filteredProducts.length} z {products.length}
              </p>

              <div className="product-list">
                {filteredProducts.map((product) => {
                  const cartItem = cartItemsByProductId.get(product.id);
                  const inCartQuantity = cartItem ? cartItem.quantity : 0;

                  return (
                    <article key={product.id} className="product-item">
                      <div>
                        <strong>{product.name}</strong>
                        <p>Kategoria: {product.category.name}</p>
                        <p>Cena: {product.price} zł</p>
                        <p>Stan magazynowy: {product.stock_quantity}</p>
                        {inCartQuantity > 0 && (
                          <p>W koszyku: {inCartQuantity} szt.</p>
                        )}
                      </div>

                      <div className="product-actions">
                        <label>
                          Ilość
                          <input
                            type="number"
                            min="1"
                            max={product.stock_quantity}
                            value={getQuantityForProduct(product.id)}
                            onChange={(event) =>
                              handleQuantityChange(
                                product.id,
                                event.target.value
                              )
                            }
                          />
                        </label>

                        <button
                          type="button"
                          disabled={product.stock_quantity <= 0}
                          onClick={() => handleAddToCart(product)}
                        >
                          {inCartQuantity > 0
                            ? "Dodaj kolejne sztuki"
                            : "Dodaj do koszyka"}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            </>
          )}
        </section>
      </main>
    </>
  );
}

export default ProductsPage;
