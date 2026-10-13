# 🎬 FlexTube — Téléchargeur & Convertisseur Vidéo/Audio Gratuit

**FlexTube** est une application web moderne inspirée de noTube, permettant de convertir et télécharger facilement des vidéos depuis **YouTube**, **TikTok** et **Pinterest** en formats audio (**MP3**, **M4A**, **WAV**) et vidéo (**MP4** jusqu'à 1080p/4K).

---

## ✨ Fonctionnalités Clés
- ⚡ **Détection automatique de plateforme :** Reconnaît instantanément les liens YouTube (Shorts inclus), TikTok et Pinterest.
- 🎵 **Formats Audio :** MP3 HD (320 kbps), MP3 (192 kbps), M4A, WAV.
- 🎬 **Formats Vidéo :** MP4 (1080p Full HD, 720p HD, 4K Ultra HD), WEBM.
- 🎨 **Interface moderne :** Mode sombre (Dark mode) et clair (Light mode), cartes en verre (glassmorphism), responsive mobile/tablette/PC.
- 📋 **Bouton Coller en 1 clic :** Intégration du presse-papier système.
- 🧪 **Boutons de test rapide :** Testez instantanément avec des exemples YouTube, TikTok ou Pinterest.
- 📜 **Historique local :** Enregistre les conversions récentes dans le navigateur (Local Storage).
- 💬 **Section FAQ & Explications :** Présentation étape par étape claire et optimisée.

---

## 🌐 Comment déployer FlexTube 100% Gratuitement en 1 Minute

### Option 1 : Déploiement instantané sur Netlify Drop (La méthode la plus rapide - 10 secondes)
1. Ouvrez votre navigateur et allez sur : **[https://app.netlify.com/drop](https://app.netlify.com/drop)**
2. Glissez-déposez simplement le dossier complet :
   `C:\Users\penda\.gemini\antigravity\scratch\flextube`
3. C'est tout ! Netlify vous génère immédiatement une adresse web sécurisée HTTPS (ex: `https://flextube.netlify.app`).

---

### Option 2 : Déploiement sur GitHub Pages (Gratuit à vie)
1. Créez un compte ou connectez-vous sur **[GitHub](https://github.com)**.
2. Créez un nouveau dépôt public nommé `flextube`.
3. Cliquez sur **Upload files** et glissez les 3 fichiers (`index.html`, `style.css`, `app.js`).
4. Allez dans **Settings** > **Pages** > sous *Branch*, choisissez `main` puis cliquez sur **Save**.
5. Votre site sera disponible à l'adresse : `https://<votre-pseudo>.github.io/flextube`.

---

### Option 3 : Déploiement sur Vercel
1. Allez sur **[https://vercel.com](https://vercel.com)** et connectez-vous.
2. Cliquez sur **Add New...** > **Project**.
3. Importez votre dépôt GitHub ou déposez votre dossier.
4. Cliquez sur **Deploy**.

---

## ⚠️ Important : GitHub Pages ne peut pas exécuter le backend de téléchargement

Le site statique hébergé sur GitHub Pages ne peut pas lancer un serveur Python/Node pour traiter les liens externes. Les téléchargements YouTube/Pinterest exigent un backend réel capable d’appeler `yt-dlp`, de convertir les fichiers et de servir les flux téléchargés.

Pour un vrai fonctionnement, il faut donc :
- garder le frontend statique sur GitHub Pages si vous le souhaitez ;
- héberger le backend Python sur un service gratuit compatible : **Render**, **Railway**, **Fly.io** ou un worker Cloudflare si vous laissez la logique côté serveur ailleurs ;
- configurer `window.FLEXTUBE_API_BASE = 'https://votre-backend.example'` dans le frontend ou ajouter une variable globale dans la page.

Le backend inclus dans ce dépôt (`server.py`) est prêt à fonctionner sur un hôte avec Python + FFmpeg ; il utilise `yt-dlp` gratuitement et sans clé API payante.
