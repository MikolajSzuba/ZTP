import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

import { apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import Navbar from "../components/Navbar";
import useCurrentOperator from "../hooks/useCurrentOperator";

function CartPage() {
  const navigate = useNavigate();
  const { authLoading, authError } = useCurrentOperator();

  const [cart, setCart] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  async function loadCart() {
    setError("");

    try {
      const data = await apiGet("/cart");
      setCart(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && !authError) {
      loadCart();
    }
  }, [authLoading, authError]);

  async function handleIncrease(item) {
    setError("");

    try {
      await apiPatch(`/cart/items/${item.id}`, {
        quantity: item.quantity + 1,
      });
      await loadCart();
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    }
  }

  async function handleDecrease(item) {
    setError("");

    if (item.quantity <= 1) {
      return;
    }

    try {
      await apiPatch(`/cart/items/${item.id}`, {
        quantity: item.quantity - 1,
      });
      await loadCart();
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    }
  }

  async function handleRemove(itemId) {
    setError("");

    try {
      await apiDelete(`/cart/items/${itemId}`);
      toast.success("Produkt został usunięty z koszyka.");
      await loadCart();
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    }
  }

  async function handleCheckout() {
    setError("");
    setCheckoutLoading(true);

    try {
      await apiPost("/cart/checkout", {});
      toast.success("Zamówienie zostało złożone.");
      navigate("/orders");
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    } finally {
      setCheckoutLoading(false);
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

  const isCartEmpty = !cart || cart.items.length === 0;

  return (
    <>
      <Navbar />

      <main className="page page-top">
        <section className="card wide-card">
          <h1>Koszyk</h1>

          {loading && <p>Ładowanie koszyka...</p>}
          {error && <p className="error">{error}</p>}

          {!loading && !error && cart && (
            <>
              <div className="details">
                <p>
                  <strong>Liczba pozycji:</strong> {cart.items_count}
                </p>
                <p>
                  <strong>Suma koszyka:</strong> {cart.total_amount} zł
                </p>
              </div>

              {cart.items.length === 0 ? (
                <p>Koszyk jest pusty.</p>
              ) : (
                <div className="product-list">
                  {cart.items.map((item) => (
                    <article key={item.id} className="product-item">
                      <div>
                        <strong>{item.product.name}</strong>
                        <p>Cena jednostkowa: {item.product.price} zł</p>
                        <p>Ilość: {item.quantity}</p>
                        <p>Cena pozycji: {item.line_total} zł</p>
                      </div>

                      <div className="product-actions">
                        <button type="button" onClick={() => handleDecrease(item)}>
                          -
                        </button>
                        <button type="button" onClick={() => handleIncrease(item)}>
                          +
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemove(item.id)}
                        >
                          Usuń
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}

              <div className="actions-bar">
                <button
                  type="button"
                  disabled={isCartEmpty || checkoutLoading}
                  onClick={handleCheckout}
                >
                  {checkoutLoading ? "Składanie zamówienia..." : "Złóż zamówienie"}
                </button>
              </div>
            </>
          )}
        </section>
      </main>
    </>
  );
}

export default CartPage;
