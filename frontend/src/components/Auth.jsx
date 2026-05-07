import React, { useState } from 'react';
import api from '../api';

const Auth = ({ onLoginSuccess }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({
        email: '', password: '', name: '', roll_number: '', dept: ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        // Match the exact backend endpoints from your main.py routers
        const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';

        try {
            const response = await api.post(endpoint, formData);

            if (isLogin) {
                // Save the token so the browser remembers you
                localStorage.setItem('token', response.data.access_token);
                onLoginSuccess(); // Tell App.jsx we are logged in!
            } else {
                alert("Registration successful! Now please login.");
                setIsLogin(true);
            }
        } catch (err) {
            alert(err.response?.data?.detail || "An error occurred");
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-base-200">
            <div className="card w-96 bg-base-100 shadow-xl">
                <div className="card-body">
                    <h2 className="card-title justify-center text-2xl font-bold">
                        {isLogin ? 'Welcome Back' : 'Create Account'}
                    </h2>
                    <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                        {!isLogin && (
                            <>
                                <input type="text" placeholder="Full Name" className="input input-bordered w-full"
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                                <input type="text" placeholder="Roll Number" className="input input-bordered w-full"
                                    onChange={(e) => setFormData({ ...formData, roll_number: e.target.value })} required />
                                <input type="text" placeholder="Department" className="input input-bordered w-full"
                                    onChange={(e) => setFormData({ ...formData, dept: e.target.value })} required />
                            </>
                        )}
                        <input type="email" placeholder="University Email" className="input input-bordered w-full"
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })} required />
                        <input type="password" placeholder="Password" className="input input-bordered w-full"
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })} required />

                        <button type="submit" className="btn btn-primary w-full">
                            {isLogin ? 'Login' : 'Sign Up'}
                        </button>
                    </form>
                    <button onClick={() => setIsLogin(!isLogin)} className="btn btn-link btn-sm mt-2">
                        {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Auth;