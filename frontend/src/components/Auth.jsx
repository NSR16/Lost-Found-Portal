import { useState } from "react";
import toast from "react-hot-toast";
import api from "../api";

const INITIAL_FORM = {
  email: "",
  password: "",
  name: "",
  roll_number: "",
  dept: "",
};

const Auth = ({ onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState(INITIAL_FORM);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const updateField = (field) => (event) => {
    setFormData((current) => ({ ...current, [field]: event.target.value }));
    setError("");
    setSuccess("");
  };

  const switchMode = () => {
    setIsLogin((current) => !current);
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);

    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
    try {
      const response = await api.post(endpoint, formData);

      if (isLogin) {
        localStorage.setItem("token", response.data.access_token);
        toast.success("Welcome back!");
        onLoginSuccess();
      } else {
        const message = "Registration successful! Now please login.";
        setSuccess(message);
        toast.success(message);
        setIsLogin(true);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const message = typeof detail === "string"
        ? detail
        : "Unable to complete your request. Check your details and try again.";
      setError(message);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-200 px-4 py-8">
      <div className="card w-full max-w-md border border-base-200 bg-base-100 shadow-xl">
        <div className="card-body">
          <div className="mb-2 text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">
              CampusLink
            </p>
            <h1 className="mt-2 text-2xl font-bold">
              {isLogin ? "Welcome Back" : "Create Account"}
            </h1>
            <p className="mt-1 text-sm text-base-content/60">
              Lost &amp; Found for your campus community
            </p>
          </div>

          {error && (
            <div className="alert alert-error mt-3 text-sm" role="alert">
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="alert alert-success mt-3 text-sm" role="status">
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-4 space-y-4" autoComplete="off">
            {!isLogin && (
              <>
                <input
                  type="text"
                  placeholder="Full Name"
                  autoComplete="off"
                  className="input input-bordered w-full"
                  value={formData.name}
                  onChange={updateField("name")}
                  required
                />
                <input
                  type="text"
                  placeholder="Roll Number"
                  autoComplete="off"
                  className="input input-bordered w-full"
                  value={formData.roll_number}
                  onChange={updateField("roll_number")}
                  required
                />
                <input
                  type="text"
                  placeholder="Department"
                  autoComplete="off"
                  className="input input-bordered w-full"
                  value={formData.dept}
                  onChange={updateField("dept")}
                  required
                />
              </>
            )}
            <input
              type="email"
              placeholder="University Email"
              autoComplete="username"
              className="input input-bordered w-full"
              value={formData.email}
              onChange={updateField("email")}
              required
            />
            <input
              type="password"
              placeholder="Password"
              autoComplete={isLogin ? "current-password" : "new-password"}
              className="input input-bordered w-full"
              value={formData.password}
              onChange={updateField("password")}
              required
            />

            <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
              {submitting ? (
                <span className="loading loading-spinner loading-sm" />
              ) : (
                isLogin ? "Login" : "Sign Up"
              )}
            </button>
          </form>

          <button type="button" onClick={switchMode} className="btn btn-link btn-sm mt-2">
            {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Auth;
