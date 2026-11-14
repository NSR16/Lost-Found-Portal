import { useState, useEffect, useCallback } from "react";
import { Toaster } from "react-hot-toast";
import toast from "react-hot-toast";
import api from "./api";

// Import your new Auth component
import Auth from "./components/Auth";

import Navbar from "./components/Navbar";
import StatsOverview from "./components/StatsOverview";
import ItemCard from "./components/ItemCard";
import ClaimModal from "./components/ClaimModal";
import ReportModal from "./components/ReportModal";
import MyItems from "./components/MyItems";

const FILTERS = ["ALL", "LOST", "FOUND"];

export default function App() {
  // ── Auth State ──────────────────────────────────────────────
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

  // ── Dashboard States ────────────────────────────────────────
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("ALL");
  const [activeSection, setActiveSection] = useState("browse");
  const [claimItem, setClaimItem] = useState(null);
  // 1. Add a new state at the top with your other states
  const [receivedClaims, setReceivedClaims] = useState([]);
  const [myClaims, setMyClaims] = useState([]);
  const [myItems, setMyItems] = useState([]);
  const [myItemsStatus, setMyItemsStatus] = useState("loading");
  const [handoffClaim, setHandoffClaim] = useState(null);
  const [handoffInstructions, setHandoffInstructions] = useState("");
  const [handoffLoading, setHandoffLoading] = useState(false);

  // 2. Add the fetch function
  const fetchReceivedClaims = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const { data } = await api.get("/api/claims/received");
      setReceivedClaims(data);
    } catch (err) {
      console.error("Failed to fetch received claims", err);
    }
  }, [isAuthenticated]);

  const fetchMyClaims = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const { data } = await api.get("/api/claims/my");
      setMyClaims(data);
    } catch (err) {
      console.error("Failed to fetch my claims", err);
    }
  }, [isAuthenticated]);

  const fetchMyItems = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const { data } = await api.get("/api/items/my");
      setMyItems(data);
      setMyItemsStatus("ready");
    } catch (err) {
      console.error("Failed to fetch my items", err);
      setMyItemsStatus("error");
    }
  }, [isAuthenticated]);

  const isOwnItem = (itemId) =>
    itemId !== null &&
    itemId !== undefined &&
    myItems.some((myItem) =>
      myItem.item_id !== null &&
      myItem.item_id !== undefined &&
      String(myItem.item_id) === String(itemId)
    );

  const handleClaimItem = (item) => {
    if (myItemsStatus !== "ready") {
      toast.error("Unable to verify item ownership. Please try again shortly.");
      return;
    }

    if (isOwnItem(item.item_id)) return;
    setClaimItem(item);
  };

  const handleRemoveItem = async (itemId) => {
    try {
      // Call the soft delete endpoint
      await api.patch(`/api/items/${itemId}/delete`);
      // Immediately update local state to remove the item
      setMyItems((prev) => prev.filter((item) => item.item_id !== itemId));
      await fetchItems(); // Refresh the main feed
      await fetchReceivedClaims(); // Refresh claims after an item is deleted
      await fetchMyClaims();
      await fetchMyItems();
      toast.success("Item removed successfully.");
    } catch (err) {
      const detail = err.response?.data?.detail;
      const message = typeof detail === "string"
        ? detail
        : err.message || "Failed to delete item.";
      toast.error(`Delete failed: ${message}`);
      console.error("Delete item error:", err);
    }
  };

  const fetchCurrentUser = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      const { data } = await api.get("/api/auth/me");
      setCurrentUser(data);
    } catch (err) {
      console.error("Failed to fetch current user", err);
      // If token is invalid, logout
      handleLogout();
    }
  }, [isAuthenticated]);

  // 3. Add the approval handler
  const handleApproveClaim = (claim) => {
    if (claim.item?.is_in_custody) {
      setHandoffClaim(claim);
      setHandoffInstructions("");
      return;
    }

    handleConfirmReceipt(claim.claim_id);
  };

  const handleScheduleHandoff = async () => {
    if (!handoffClaim) return;
    setHandoffLoading(true);
    try {
      const { data: updatedClaim } = await api.patch(`/api/claims/${handoffClaim.claim_id}/status`, {
        status: "APPROVED",
        handoff_instructions: handoffInstructions,
      });

      // 1. Update the 'Received' list (The one with the Approve button)
      setReceivedClaims((prev) => 
        prev.map((c) => (c.claim_id === updatedClaim.claim_id ? updatedClaim : c))
      );

      // 2. Update the 'My Claims' list (if visible)
      setMyClaims((prev) => 
        prev.map((c) => (c.claim_id === updatedClaim.claim_id ? updatedClaim : c))
      );

      // 3. Close the modal and reset
      setHandoffClaim(null);
      setHandoffInstructions("");
      
      // 4. Refresh claim and item state after handoff update
      await fetchReceivedClaims();
      await fetchMyClaims();
      await fetchItems();
      await fetchMyItems();
      toast.success("Handoff instructions sent.");

    } catch (err) {
      console.error("Handoff Error:", err);
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to send handoff instructions.");
    } finally {
      setHandoffLoading(false);
    }
  };

  const handleConfirmReceipt = async (claimId) => {
    try {
      await api.patch(`/api/claims/${claimId}/status`, { status: "APPROVED" });
      await fetchItems();
      await fetchReceivedClaims();
      await fetchMyClaims();
      await fetchMyItems();
      toast.success("Claim approved.");
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to confirm receipt.");
    }
  };

  // 4. Update the stats object to use the actual length
  const stats = {
    totalLost: items.filter((i) => i.type === "LOST").length,
    totalFound: items.filter((i) => i.type === "FOUND").length,
    activeClaims: receivedClaims.length, // Now dynamic!
  };

  // Check for token on startup
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const fetchItems = useCallback(async () => {
    if (!isAuthenticated) return; // Don't fetch if not logged in

    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (activeFilter !== "ALL") params.type = activeFilter;
      if (search.trim()) params.search = search.trim();

      const { data } = await api.get("/api/items", { params });
      setItems(data);
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout(); // Kick user out if token is expired
      } else {
        setError("Could not connect to the server. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  }, [activeFilter, search, isAuthenticated]);



  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsAuthenticated(false);
    setCurrentUser(null);
    setClaimItem(null);
    setMyItems([]);
    setMyItemsStatus("loading");
  };

  useEffect(() => {
    if (!isAuthenticated) return;

    setLoading(true);
    setError(null);

    // Debounce: wait 300ms after the user STOPS typing/changing filter
    const timer = setTimeout(() => {
      // Now we make the API call
      fetchItems();
      fetchReceivedClaims();
      fetchMyClaims();
      fetchMyItems();
      fetchCurrentUser();
    }, 300);

    // Cleanup: If the user types again before 300ms, cancel the old timer
    return () => clearTimeout(timer);

  }, [fetchItems, fetchReceivedClaims, fetchMyClaims, fetchMyItems, fetchCurrentUser, isAuthenticated]); // Added isAuthenticated dependency


  // ── Conditional Rendering ───────────────────────────────────

  // If not logged in, show ONLY the Auth screen
  if (!isAuthenticated) {
    return (
      <div data-theme="cupcake">
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#fffaf3",
              color: "#273a3b",
              border: "1px solid #d9e8e7",
              borderRadius: "14px",
            },
            success: { iconTheme: { primary: "#4EA5AD", secondary: "#fffaf3" } },
          }}
        />
        <Auth onLoginSuccess={() => setIsAuthenticated(true)} />
      </div>
    );
  }

  // If logged in, show the Dashboard
  return (
    <div data-theme="cupcake" className="min-h-screen bg-base-200">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#fffaf3",
            color: "#273a3b",
            border: "1px solid #d9e8e7",
            borderRadius: "14px",
          },
          success: { iconTheme: { primary: "#4EA5AD", secondary: "#fffaf3" } },
        }}
      />

      <Navbar
        search={search}
        onSearch={setSearch}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        myClaimsCount={myClaims.length}
        onLogout={handleLogout}
        currentUser={currentUser}
      />

      <div className="lg:ml-64">
      <main className="max-w-6xl mx-auto px-4 pb-8 pt-24 space-y-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-base-content">
            Lost &amp; Found Portal
          </h1>
          <p className="text-base-content/60 mt-1">
            Welcome back! Search for lost items or report something you found.
          </p>
        </div>

        {activeSection === "browse" && (
          <>
            <StatsOverview data={stats} />

            <section className="mb-8 bg-base-100 p-6 rounded-[2rem] shadow-sm border border-base-200">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-2xl font-semibold">Available Items</h2>
              <p className="text-sm text-base-content/60 mt-1">
                Browse the latest items reported in the last 30 days.
              </p>
            </div>
            <span className="text-sm text-base-content/50">
              {loading ? "Fetching…" : `${items.length} item${items.length !== 1 ? "s" : ""}`}
            </span>
          </div>

          <div className="mt-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap gap-2">
              {FILTERS.map((f) => (
                <button
                  key={f}
                  className={`btn btn-sm rounded-full ${
                    activeFilter === f ? "btn-primary" : "btn-ghost"
                  }`}
                  onClick={() => setActiveFilter(f)}
                >
                  {f === "ALL" ? "All" : f === "LOST" ? "🔴 Lost" : "🟢 Found"}
                </button>
              ))}
            </div>
            <div className="w-full lg:w-auto">
              <span className="text-sm text-base-content/60">
                Filter the feed and claim items that match your needs.
              </span>
            </div>
          </div>
            </section>

            <section className="bg-base-100 p-6 rounded-[2rem] shadow-sm border border-base-200">
          {loading && (
            <div className="flex justify-center items-center py-24">
              <span className="loading loading-spinner loading-lg text-primary" />
            </div>
          )}

          {!loading && error && (
            <div className="alert alert-error max-w-lg mx-auto">
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-24 text-base-content/40 gap-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-20 h-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-lg font-medium">No items found</p>
              <p className="text-sm">Try a different filter or be the first to report!</p>
              <button className="btn btn-primary btn-sm" onClick={() => setActiveSection("report")}>
                Report an Item
              </button>
            </div>
          )}

          {!loading && !error && items.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {items.map((item) => (
                <ItemCard
                  key={item.item_id}
                  item={item}
                  isOwnItem={isOwnItem(item.item_id)}
                  ownershipStatus={myItemsStatus}
                  onClaim={handleClaimItem}
                />
              ))}
            </div>
          )}
            </section>
          </>
        )}

        {activeSection === "report" && (
          <ReportModal
            inline
            onSuccess={async () => {
              setMyItemsStatus("loading");
              await fetchItems();
              await fetchMyItems();
            }}
          />
        )}

        {activeSection === "claims" && (
          <>
            <MyItems items={myItems} onRemove={handleRemoveItem} />

            {/* Manage Received Claims Section */}
          <div className="mb-10 bg-base-100 p-6 rounded-2xl shadow-sm border border-base-200">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              🔔 Claims on Your Items
            </h2>
            <div className="overflow-x-auto">
              <table className="table w-full">
                <thead>
                  <tr className="bg-base-200">
                    <th>Item</th>
                    <th>Requested By</th>
                    <th>Status</th>
                    <th>Message/Proof</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {receivedClaims.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center py-8 text-base-content/60">
                        No claims on your items yet.
                      </td>
                    </tr>
                  ) : (
                    receivedClaims.map((claim) => (
                      <tr key={claim.claim_id} className="hover">
                        <td className="font-medium">{claim.item?.title || "Unknown Item"}</td>
                        <td>{claim.claimer?.name || "Unknown"} ({claim.claimer?.roll_number || "—"})</td>
                        <td>
                          <span className={`badge ${
                            claim.status === "APPROVED" ? "badge-success" :
                            claim.status === "REJECTED" ? "badge-error" :
                            "badge-outline"
                          }`}>
                            {claim.status}
                          </span>
                        </td>
                        <td className="max-w-xs truncate">{claim.proof_description || "—"}</td>
                        <td>
                          {claim.status === "PENDING" ? (
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => handleApproveClaim(claim)}
                            >
                              Approve
                            </button>
                          ) : (
                            <span className="text-sm text-base-content/60">No action</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

            {/* My Claims Status Section */}
            <div className="mb-10 bg-base-100 p-6 rounded-2xl shadow-sm border border-base-200">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            📋 My Claims Status
          </h2>
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr className="bg-base-200">
                  <th>Item</th>
                  <th>Status</th>
                  <th>Submitted</th>
                  <th>Owner Contact</th>
                  <th>Meeting Info</th>
                </tr>
              </thead>
              <tbody>
                {myClaims.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-base-content/60">
                      No claims yet.
                    </td>
                  </tr>
                ) : (
                  myClaims.map((claim) => (
                    <tr key={claim.claim_id} className="hover">
                      <td className="font-medium">{claim.item?.title || "Unknown Item"}</td>
                      <td>
                        <span className={`badge ${
                          claim.status === "APPROVED" ? "badge-success" :
                          claim.status === "REJECTED" ? "badge-error" :
                          "badge-outline"
                        }`}>
                          {claim.status}
                        </span>
                      </td>
                      <td>{new Date(claim.created_at).toLocaleDateString()}</td>
                      <td>{claim.owner_contact || "—"}</td>
                      <td className="max-w-xs truncate">
                        {claim.handoff_instructions || claim.item?.location || "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
              </div>
            </div>
            </>
          )}
      </main>

      {handoffClaim && (
        <dialog className="modal modal-open">
          <div className="modal-box w-full max-w-md">
            <h3 className="font-bold text-lg mb-3">Handoff Instructions</h3>
            <p className="text-sm text-base-content/60 mb-4">
              This item is in custody. Add a short location or pickup note for the claimant.
            </p>
            <textarea
              className="textarea textarea-bordered w-full h-28 text-sm"
              placeholder="e.g. Meet me at the Library Front Desk after 4 PM."
              value={handoffInstructions}
              onChange={(e) => setHandoffInstructions(e.target.value)}
              required
            />
            <div className="modal-action mt-0">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setHandoffClaim(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={handleScheduleHandoff}
                disabled={handoffLoading || !handoffInstructions.trim()}
              >
                {handoffLoading ? <span className="loading loading-spinner loading-xs" /> : "Send Instructions"}
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={() => setHandoffClaim(null)} />
        </dialog>
      )}

      <footer className="footer footer-center p-6 mt-10 bg-base-100 text-base-content/50 text-sm border-t border-base-200">
        <p>CampusLink Lost &amp; Found Portal — DBMS Project © 2025</p>
      </footer>
      </div>

      {claimItem && myItemsStatus === "ready" && !isOwnItem(claimItem.item_id) && (
        <ClaimModal item={claimItem} onClose={() => setClaimItem(null)} />
      )}
    </div>
  );
}