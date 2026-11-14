import { X, Upload } from "lucide-react";
import { useState } from "react";
import api from "../api";
import toast from "react-hot-toast";

const CATEGORIES = [
  { id: 1, name: "Electronics" },
  { id: 2, name: "Documents" },
  { id: 3, name: "Keys" },
  { id: 4, name: "Clothing" },
  { id: 5, name: "Accessories" },
  { id: 6, name: "Sports" },
  { id: 7, name: "Stationery" },
  { id: 8, name: "Other" },
];

const EMPTY = {
  title: "",
  description: "",
  type: "LOST",
  location: "",
  category_id: 1,
  image_url: "",
  is_in_custody: false,
};

export default function ReportModal({ inline = false, onClose, onSuccess }) {
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(false);

  function update(field, val) {
    setForm((f) => ({ ...f, [field]: val }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/api/items", {
        ...form,
        category_id: Number(form.category_id),
      });
      toast.success("Item reported successfully!");
      setForm({ ...EMPTY });
      onSuccess?.();
      onClose?.();
    } catch (err) {
      const msg = err.response?.data?.detail ?? "Failed to report item.";
      toast.error(typeof msg === "string" ? msg : "Please log in first.");
    } finally {
      setLoading(false);
    }
  }

  const formContent = (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {/* Type toggle */}
          <div className="flex gap-2">
            {["LOST", "FOUND"].map((t) => (
              <button
                key={t}
                type="button"
                className={`btn btn-sm flex-1 ${form.type === t ? (t === "LOST" ? "btn-error" : "btn-success") : "btn-ghost"}`}
                onClick={() => update("type", t)}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Title */}
          <input
            type="text"
            className="input input-bordered input-sm w-full"
            placeholder="Item title (e.g. Blue JBL Earbuds)"
            value={form.title}
            onChange={(e) => update("title", e.target.value)}
            required
          />

          {/* Description */}
          <textarea
            className="textarea textarea-bordered w-full h-24 text-sm"
            placeholder="Description — color, brand, distinguishing marks…"
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
          />

          <div className="grid grid-cols-2 gap-2">
            {/* Category */}
            <select
              className="select select-bordered select-sm"
              value={form.category_id}
              onChange={(e) => update("category_id", e.target.value)}
            >
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            {/* Location */}
            <input
              type="text"
              className="input input-bordered input-sm"
              placeholder="Location (e.g. Library)"
              value={form.location}
              onChange={(e) => update("location", e.target.value)}
            />
          </div>

          {/* In Custody Checkbox (for FOUND items) */}
          {form.type === "FOUND" && (
            <div className="form-control">
              <label className="cursor-pointer label">
                <span className="label-text">I have this item in my possession</span>
                <input
                  type="checkbox"
                  className="checkbox checkbox-primary"
                  checked={form.is_in_custody}
                  onChange={(e) => update("is_in_custody", e.target.checked)}
                />
              </label>
            </div>
          )}

          {/* Image URL */}
          <input
            type="text"
            className="input input-bordered input-sm w-full"
            placeholder="Image URL (optional)"
            value={form.image_url}
            onChange={(e) => update("image_url", e.target.value)}
          />

          <div className="modal-action mt-0">
            {!inline && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
                Cancel
              </button>
            )}
            <button type="submit" className="btn btn-primary btn-sm" disabled={loading}>
              {loading ? <span className="loading loading-spinner loading-xs" /> : "Submit"}
            </button>
          </div>
    </form>
  );

  if (inline) {
    return (
      <section className="mx-auto w-full max-w-3xl rounded-[2rem] border border-base-200 bg-base-100 p-6 shadow-sm sm:p-8">
        <h2 className="mb-2 flex items-center gap-2 text-2xl font-bold">
          <Upload size={20} className="text-primary" />
          Report a Lost / Found Item
        </h2>
        <p className="mb-6 text-sm text-base-content/60">
          Add details to help the campus community identify and return the item.
        </p>
        {formContent}
      </section>
    );
  }

  return (
    <dialog className="modal modal-open">
      <div className="modal-box w-full max-w-lg">
        <button
          className="btn btn-sm btn-circle btn-ghost absolute right-3 top-3"
          onClick={onClose}
        >
          <X size={16} />
        </button>
        <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
          <Upload size={18} /> Report a Lost / Found Item
        </h3>
        {formContent}
      </div>
      <div className="modal-backdrop" onClick={onClose} />
    </dialog>
  );
}
