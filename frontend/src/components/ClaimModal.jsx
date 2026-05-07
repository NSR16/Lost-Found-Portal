import { X, Send } from "lucide-react";
import { useState } from "react";
import api from "../api";
import toast from "react-hot-toast";

export default function ClaimModal({ item, onClose }) {
  const [proof, setProof] = useState("");
  const [loading, setLoading] = useState(false);

  if (!item) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/api/claims", {
        item_id: item.item_id,
        proof_description: proof,
      });
      toast.success(
        item.type === "FOUND"
          ? "Claim submitted! The finder will review it."
          : "Report submitted! The owner will be notified."
      );
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail ?? "Failed to submit claim.";
      toast.error(typeof msg === "string" ? msg : "Please log in first.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <dialog className="modal modal-open">
      <div className="modal-box w-full max-w-md">
        <button
          className="btn btn-sm btn-circle btn-ghost absolute right-3 top-3"
          onClick={onClose}
        >
          <X size={16} />
        </button>
        <h3 className="font-bold text-lg mb-1">Claim: {item.title}</h3>
        <p className="text-sm text-base-content/60 mb-4">
          {item.type === "FOUND"
            ? "Describe how you can prove this item belongs to you (receipt, photo, serial number, etc.)"
            : "Describe where and how you found this item (location, circumstances, etc.)"
          }
        </p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <textarea
            className="textarea textarea-bordered w-full h-28 text-sm"
            placeholder={
              item.type === "FOUND"
                ? "e.g. My phone case has a scratch on the bottom-right corner and my name is written inside..."
                : "e.g. I found this item in the library on the 2nd floor near the computer lab..."
            }
            value={proof}
            onChange={(e) => setProof(e.target.value)}
            required
          />
          <div className="modal-action mt-0">
            <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary btn-sm gap-1" disabled={loading}>
              {loading ? <span className="loading loading-spinner loading-xs" /> : <Send size={14} />}
              {item.type === "FOUND" ? "Submit Claim" : "Report Found"}
            </button>
          </div>
        </form>
      </div>
      <div className="modal-backdrop" onClick={onClose} />
    </dialog>
  );
}
