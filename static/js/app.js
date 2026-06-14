// Fonction utilitaire pour faire des appels API proprement
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {},
        credentials: 'include'
    };

    if (body) {
        if (body instanceof FormData) {
            options.body = body;
            // Ne surtout PAS forcer le 'Content-Type' avec FormData
            // Le navigateur s'occupe de mettre 'multipart/form-data' tout seul
        } else {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
    }

    try {
        const response = await fetch(`/api${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.msg || "Une erreur est survenue sur le serveur");
        }
        return data;
    } catch (error) {
        showMessage(error.message, "error");
        throw error;
    }
}

// Fonction pour afficher des messages à l'utilisateur
function showMessage(text, type = "success") {
    const msgBox = document.getElementById("message-box");
    if (!msgBox) return;
    
    msgBox.textContent = text;
    msgBox.className = type;
    msgBox.style.display = "block";
    
    setTimeout(() => {
        msgBox.style.display = "none";
    }, 5000);
}

// Fonction globale pour se déconnecter
async function logout() {
    try {
        await apiCall('/auth/logout', 'POST');
        window.location.href = '/login';
    } catch (e) {
        console.error("Erreur lors de la déconnexion", e);
    }
}