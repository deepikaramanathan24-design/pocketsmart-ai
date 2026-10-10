async function postJSON(url, data) {
    const response = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });
    return await response.json();
}

const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const data = {
            name: document.getElementById("name").value,
            email: document.getElementById("email").value,
            password: document.getElementById("password").value
        };

        const result = await postJSON("/register", data);
        document.getElementById("message").textContent = result.message;

        if (result.message === "Registration successful") {
            setTimeout(() => window.location.href = "/login", 800);
        }
    });
}

const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const result = await postJSON("/login", {
            email: document.getElementById("email").value,
            password: document.getElementById("password").value
        });

        document.getElementById("message").textContent = result.message;

       if (result.success === true) {
            localStorage.setItem("user_id", result.user_id);
            window.location.href = "/dashboard?user_id=" + result.user_id;
        }
    });
}

const resetForm = document.getElementById("resetForm");

if (resetForm) {
    resetForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const result = await postJSON("/forgot-password", {
            email: document.getElementById("email").value,
            new_password: document.getElementById("new_password").value
        });

        document.getElementById("message").textContent = result.message;
    });
}
