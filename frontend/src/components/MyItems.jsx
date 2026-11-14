export default function MyItems({ items, onRemove }) {
  return (
    <div className="mb-10 bg-base-100 p-6 rounded-2xl shadow-sm border border-base-200">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        🏷️ My Posted Items
      </h2>
      <div className="overflow-x-auto">
        <table className="table w-full">
          <thead>
            <tr className="bg-base-200">
              <th>Title</th>
              <th>Type</th>
              <th>Status</th>
              <th>Posted</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-base-content/60">
                  You have not reported any items yet.
                </td>
              </tr>
            ) : items.map((item) => (
              <tr key={item.item_id} className="hover">
                <td className="font-medium">{item.title}</td>
                <td>{item.type}</td>
                <td>
                  <span className={`badge ${
                    item.status === "RESOLVED" ? "badge-success" :
                    item.status === "REMOVED" ? "badge-error" :
                    "badge-outline"
                  }`}>
                    {item.status}
                  </span>
                </td>
                <td>{new Date(item.posted_at).toLocaleDateString()}</td>
                <td>
                  {item.status === "ACTIVE" ? (
                    <button
                      className="btn btn-sm btn-warning"
                      onClick={() => onRemove(item.item_id)}
                    >
                      Delete
                    </button>
                  ) : (
                    <span className="text-sm text-base-content/50">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
