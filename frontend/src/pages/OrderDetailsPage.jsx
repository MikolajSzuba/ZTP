import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "react-toastify";

import { apiGet, apiRequest } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Navbar from "../components/Navbar";
import StatusBadge from "../components/StatusBadge";
import useCurrentOperator from "../hooks/useCurrentOperator";

function OrderDetailsPage() {
  const { orderId } = useParams();
  const { authLoading, authError } = useCurrentOperator();

  const [order, setOrder] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [loading, setLoading] = useState(true);
  const [completeLoading, setCompleteLoading] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);

  const loadOrderDetails = useCallback(async () => {
    setLoadError("");

    try {
      const data = await apiGet(`/orders/${orderId}`);
      setOrder(data);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (!authLoading && !authError) {
      loadOrderDetails();
    }
  }, [authLoading, authError, loadOrderDetails]);

  async function handleCompleteOrder() {
    setActionError("");
    setCompleteLoading(true);

    try {
      await apiRequest(`/orders/${orderId}/complete`, {
        method: "POST",
        headers: {
          "Idempotency-Key": crypto.randomUUID(),
        },
      });

      toast.success("Zamówienie zostało zakończone.");
      await loadOrderDetails();
    } catch (err) {
      setActionError(err.message);
      toast.error(err.message);
    } finally {
      setCompleteLoading(false);
    }
  }

  async function handleCancelOrder() {
    const confirmed = window.confirm(
      "Czy na pewno chcesz anulować to zamówienie?"
    );

    if (!confirmed) {
      return;
    }

    setActionError("");
    setCancelLoading(true);

    try {
      await apiRequest(`/orders/${orderId}/cancel`, {
        method: "POST",
      });

      toast.success("Zamówienie zostało anulowane.");
      await loadOrderDetails();
    } catch (err) {
      setActionError(err.message);
      toast.error(err.message);
    } finally {
      setCancelLoading(false);
    }
  }

  if (authLoading) {
    return (
      <main className="page">
        <section className="card">
          <LoadingState message="Sprawdzanie sesji..." />
        </section>
      </main>
    );
  }

  if (authError) {
    return null;
  }

  const isActionLoading = completeLoading || cancelLoading;

  return (
    <>
      <Navbar />

      <main className="page page-top">
        <section className="card wide-card">
          <Link to="/orders" className="back-link">
            ← Wróć do historii
          </Link>

          <h1>Szczegóły zamówienia</h1>

          {loading && (
            <LoadingState message="Ładowanie szczegółów zamówienia..." />
          )}

          {loadError && <ErrorState message={loadError} />}

          {actionError && <ErrorState message={actionError} />}

          {!loading && !loadError && order && (
            <>
              <div className="details">
                <p>
                  <strong>Numer:</strong> {order.order_number}
                </p>
                <p>
                  <strong>Status:</strong> <StatusBadge status={order.status} />
                </p>
                <p>
                  <strong>Suma:</strong> {order.total_amount} zł
                </p>
              </div>

              {order.status === "PENDING" ? (
                <div className="actions-bar">
                  <button
                    type="button"
                    disabled={isActionLoading}
                    onClick={handleCompleteOrder}
                  >
                    {completeLoading
                      ? "Kończenie zamówienia..."
                      : "Zakończ zamówienie"}
                  </button>

                  <button
                    type="button"
                    disabled={isActionLoading}
                    onClick={handleCancelOrder}
                  >
                    {cancelLoading ? "Anulowanie..." : "Anuluj zamówienie"}
                  </button>
                </div>
              ) : (
                <div className="info-box">
                  <p>
                    To zamówienie ma status <strong>{order.status}</strong> i
                    nie można wykonać na nim kolejnej operacji zmiany statusu.
                  </p>
                </div>
              )}

              {order.items.length === 0 ? (
                <EmptyState title="Brak produktów w zamówieniu." />
              ) : (
                <div className="product-list">
                  {order.items.map((item) => (
                    <article key={item.id} className="product-item">
                      <div>
                        <strong>{item.product_name}</strong>
                        <p>Cena jednostkowa: {item.unit_price} zł</p>
                        <p>Ilość: {item.quantity}</p>
                        <p>Cena pozycji: {item.line_total} zł</p>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </>
  );
}

export default OrderDetailsPage;
