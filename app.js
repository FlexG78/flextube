/**
 * FlexTube — Universal Video & Audio Converter
 * 100% In-App Playable Video & Audio with Direct Zero-Redirect Downloads
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const themeToggle = document.getElementById('themeToggle');
  const downloadForm = document.getElementById('downloadForm');
  const urlInput = document.getElementById('urlInput');
  const pasteBtn = document.getElementById('pasteBtn');
  const clearBtn = document.getElementById('clearBtn');
  const platformIconWrap = document.getElementById('platformIconWrap');
  const formatSelect = document.getElementById('formatSelect');
  const submitBtn = document.getElementById('submitBtn');
  
  const conversionStatus = document.getElementById('conversionStatus');
  const statusMessage = document.getElementById('statusMessage');
  const statusPercent = document.getElementById('statusPercent');
  const progressBar = document.getElementById('progressBar');
  
  const resultCard = document.getElementById('resultCard');
  const resultThumb = document.getElementById('resultThumb');
  const resultVideoPlayer = document.getElementById('resultVideoPlayer');
  const resultAudioPlayer = document.getElementById('resultAudioPlayer');
  const resultTitle = document.getElementById('resultTitle');
  const resultAuthor = document.getElementById('resultAuthor');
  const resultDuration = document.getElementById('resultDuration');
  const resultPlatformBadge = document.getElementById('resultPlatformBadge');
  const resultFormatBadge = document.getElementById('resultFormatBadge');
  const resultSizeBadge = document.getElementById('resultSizeBadge');
  const downloadLinkBtn = document.getElementById('downloadLinkBtn');
  const downloadBtnText = document.getElementById('downloadBtnText');
  const copyLinkBtn = document.getElementById('copyLinkBtn');
  const resetBtn = document.getElementById('resetBtn');

  const sampleChips = document.querySelectorAll('.sample-chip');
  const historySection = document.getElementById('historySection');
  const historyList = document.getElementById('historyList');
  const clearHistoryBtn = document.getElementById('clearHistoryBtn');
  const toastContainer = document.getElementById('toastContainer');

  // Platform SVG Icons
  const platformIcons = {
    default: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>`,
    youtube: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>`,
    tiktok: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.53.02C13.84 0 15.14.01 16.44 0c.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>`,
    pinterest: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738.098.119.112.224.083.345-.09.375-.291 1.199-.332 1.357-.053.224-.174.271-.4.164-1.49-.694-2.42-2.875-2.42-4.627 0-3.769 2.739-7.229 7.892-7.229 4.144 0 7.365 2.953 7.365 6.899 0 4.117-2.595 7.431-6.199 7.431-1.211 0-2.348-.63-2.738-1.374 0 0-.599 2.282-.744 2.84-.282 1.084-1.064 2.456-1.549 3.235C9.584 23.815 10.77 24 12 24c6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/></svg>`
  };

  // State
  const API_BASE_URL = (() => {
    const configured = (window.FLEXTUBE_API_BASE || '').trim().replace(/\/$/, '');
    if (configured) return configured;
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    return '';
  })();
  let currentConversionData = null;

  // Initialize Theme
  const savedTheme = localStorage.getItem('flextube-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);

  themeToggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const target = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', target);
    localStorage.setItem('flextube-theme', target);
    showToast(`Thème ${target === 'dark' ? 'sombre' : 'clair'} activé`, 'info');
  });

  // URL Input Events
  urlInput.addEventListener('input', () => {
    handleUrlChange(urlInput.value.trim());
  });

  clearBtn.addEventListener('click', () => {
    urlInput.value = '';
    handleUrlChange('');
    urlInput.focus();
  });

  // Paste Button Action
  pasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        urlInput.value = text.trim();
        handleUrlChange(urlInput.value);
        showToast('Lien collé avec succès !', 'success');
      }
    } catch (err) {
      showToast('Presse-papier inaccessible. Collez manuellement.', 'error');
      urlInput.focus();
    }
  });

  // Sample Chips Click
  sampleChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const sampleUrl = chip.getAttribute('data-url');
      urlInput.value = sampleUrl;
      handleUrlChange(sampleUrl);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      // Trigger conversion automatically
      setTimeout(() => {
        downloadForm.dispatchEvent(new Event('submit'));
      }, 250);
    });
  });

  // Platform Detection
  function detectPlatform(url) {
    if (!url) return null;
    const lower = url.toLowerCase();
    if (lower.includes('youtube.com') || lower.includes('youtu.be')) return 'youtube';
    if (lower.includes('tiktok.com')) return 'tiktok';
    if (lower.includes('pinterest.') || lower.includes('pin.it')) return 'pinterest';
    return 'generic';
  }

  function handleUrlChange(url) {
    clearBtn.style.display = url ? 'flex' : 'none';
    const platform = detectPlatform(url);

    platformIconWrap.className = 'platform-icon-wrap';
    if (platform === 'youtube') {
      platformIconWrap.classList.add('youtube');
      platformIconWrap.innerHTML = platformIcons.youtube;
    } else if (platform === 'tiktok') {
      platformIconWrap.classList.add('tiktok');
      platformIconWrap.innerHTML = platformIcons.tiktok;
    } else if (platform === 'pinterest') {
      platformIconWrap.classList.add('pinterest');
      platformIconWrap.innerHTML = platformIcons.pinterest;
    } else {
      platformIconWrap.innerHTML = platformIcons.default;
    }
  }

  // Extract YouTube ID
  function getYouTubeId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  }

  // Handle Form Submit (Conversion Flow)
  downloadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) {
      showToast('Veuillez saisir une URL valide.', 'error');
      return;
    }

    const platform = detectPlatform(url);
    const selectedFormat = formatSelect.value;
    const formatName = formatSelect.options[formatSelect.selectedIndex].text;
    const isAudio = selectedFormat.startsWith('mp3') || selectedFormat === 'm4a' || selectedFormat === 'wav';

    // UI state
    submitBtn.disabled = true;
    resultCard.style.display = 'none';
    conversionStatus.style.display = 'block';
    updateProgress(15, 'Connexion à la source et extraction du flux...');

    try {
      let meta = null;
      if (platform === 'tiktok') {
        meta = await resolveTikTokMedia(url, isAudio);
      } else if (platform === 'youtube') {
        meta = await resolveYouTubeMedia(url, selectedFormat, isAudio);
      } else if (platform === 'pinterest') {
        meta = await resolvePinterestMedia(url, isAudio);
      } else {
        meta = await resolveGenericMedia(url, isAudio);
      }

      updateProgress(50, `Flux détecté : "${meta.title.substring(0, 32)}..."`);
      await delay(350);

      updateProgress(80, `Préparation de la lecture et du fichier ${isAudio ? 'Audio' : 'Vidéo'}...`);
      await delay(350);

      updateProgress(100, 'Vidéo prête à être lue et téléchargée !');
      await delay(250);

      // Render Result Card (100% In-App)
      renderResult(meta, selectedFormat, formatName, url, platform);
      
      // Save to Local History
      saveToHistory({
        title: meta.title,
        author: meta.author,
        thumb: meta.thumb,
        format: formatName.split('(')[0].trim(),
        platform: meta.platformName,
        url: url,
        date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });

      showToast('Média extrait avec succès !', 'success');
    } catch (err) {
      console.error(err);
      const message = err && err.message ? err.message : 'Erreur lors du traitement du lien. Veuillez réessayer.';
      showToast(message, 'error');
    } finally {
      submitBtn.disabled = false;
      conversionStatus.style.display = 'none';
    }
  });

  // 1. TikTok Resolver (TikWM API, no fake fallback)
  async function resolveTikTokMedia(url, isAudio) {
    const response = await fetch('https://www.tikwm.com/api/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `url=${encodeURIComponent(url)}`
    });

    if (!response.ok) {
      throw new Error('Le service TikTok n’a pas répondu correctement.');
    }

    const json = await response.json();
    if (json.code !== 0 || !json.data) {
      throw new Error(json?.msg || 'Le lien TikTok est invalide ou inaccessible.');
    }

    const directMedia = isAudio ? json.data.music : json.data.play;
    return {
      title: json.data.title || 'Vidéo TikTok',
      author: json.data.author?.nickname || '@tiktok',
      thumb: json.data.cover || 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500&auto=format&fit=crop&q=80',
      duration: `${Math.floor((json.data.duration || 30) / 60)}:${String((json.data.duration || 30) % 60).padStart(2, '0')}`,
      platformName: 'TikTok',
      realMediaUrl: directMedia,
      videoStreamUrl: json.data.play,
      audioStreamUrl: json.data.music,
      isPlayableDirect: true
    };
  }

  // 2. YouTube Resolver (real backend extraction, no mock demo stream)
  async function resolveYouTubeMedia(url, formatKey, isAudio) {
    if (!API_BASE_URL) {
      throw new Error('Backend non configuré. Définissez window.FLEXTUBE_API_BASE sur l’URL publique de votre backend Python (Render/Railway/Fly.io).');
    }

    const response = await fetch(`${API_BASE_URL}/api/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, format: formatKey, platform: 'youtube' })
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || 'Le backend YouTube n’a pas pu traiter ce lien.');
    }

    return {
      title: payload.title,
      author: payload.author,
      thumb: payload.thumb,
      duration: payload.duration,
      platformName: payload.platformName,
      realMediaUrl: new URL(payload.downloadUrl, API_BASE_URL).toString(),
      videoStreamUrl: new URL(payload.videoStreamUrl, API_BASE_URL).toString(),
      audioStreamUrl: new URL(payload.audioStreamUrl, API_BASE_URL).toString(),
      isPlayableDirect: true
    };
  }

  // 3. Pinterest Resolver (real backend extraction, no mock stream)
  async function resolvePinterestMedia(url, isAudio) {
    if (!API_BASE_URL) {
      throw new Error('Backend non configuré. Définissez window.FLEXTUBE_API_BASE sur l’URL publique de votre backend Python (Render/Railway/Fly.io).');
    }

    const response = await fetch(`${API_BASE_URL}/api/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, format: 'mp4-1080', platform: 'pinterest' })
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || 'Le backend Pinterest n’a pas pu traiter ce lien.');
    }

    return {
      title: payload.title,
      author: payload.author,
      thumb: payload.thumb,
      duration: payload.duration,
      platformName: payload.platformName,
      realMediaUrl: new URL(payload.downloadUrl, API_BASE_URL).toString(),
      videoStreamUrl: new URL(payload.videoStreamUrl, API_BASE_URL).toString(),
      audioStreamUrl: new URL(payload.audioStreamUrl, API_BASE_URL).toString(),
      isPlayableDirect: true
    };
  }

  // 4. Generic Media Resolver
  async function resolveGenericMedia(url, isAudio) {
    throw new Error('Lien non pris en charge. Utilisez une URL YouTube, TikTok ou Pinterest valide.');
  }

  // Render Result in UI (Zero External Redirects)
  function renderResult(meta, formatKey, formatName, originalUrl, platform) {
    // Stop any previously playing video or audio
    resultVideoPlayer.pause();
    resultAudioPlayer.pause();
    resultVideoPlayer.style.display = 'none';
    resultAudioPlayer.style.display = 'none';
    resultThumb.style.display = 'none';

    resultTitle.textContent = meta.title;
    resultAuthor.textContent = meta.author;
    resultDuration.textContent = meta.duration;
    resultPlatformBadge.textContent = meta.platformName;
    resultFormatBadge.textContent = formatName.split('(')[0].trim();

    const isAudio = formatKey.startsWith('mp3') || formatKey === 'm4a' || formatKey === 'wav';
    resultSizeBadge.textContent = isAudio ? '~ 6.4 Mo' : '~ 28.5 Mo';

    // File name for direct download
    const extension = isAudio ? 'mp3' : 'mp4';
    const cleanFileName = `${meta.title.replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 35)}.${extension}`;

    // Inline Media Player:
    // If Video requested, show and load <video> player directly
    if (!isAudio && meta.videoStreamUrl) {
      resultVideoPlayer.src = meta.videoStreamUrl;
      resultVideoPlayer.poster = meta.thumb;
      resultVideoPlayer.style.display = 'block';
    } 
    // If Audio requested, show thumbnail + audio player
    else if (isAudio && meta.audioStreamUrl) {
      resultThumb.src = meta.thumb;
      resultThumb.style.display = 'block';
      resultAudioPlayer.src = meta.audioStreamUrl;
      resultAudioPlayer.style.display = 'block';
    } 
    else {
      resultThumb.src = meta.thumb;
      resultThumb.style.display = 'block';
    }

    // Direct Download Button (triggers direct download in-app)
    downloadLinkBtn.href = meta.realMediaUrl;
    downloadLinkBtn.setAttribute('download', cleanFileName);
    downloadBtnText.textContent = isAudio ? "Télécharger le fichier Audio (MP3)" : "Télécharger la vidéo (MP4)";

    // Force direct download behavior (no new tabs or redirecting away)
    downloadLinkBtn.onclick = (e) => {
      // Direct trigger
      showToast(`Téléchargement de "${cleanFileName}" lancé !`, 'success');
    };

    currentConversionData = {
      title: meta.title,
      downloadUrl: meta.realMediaUrl,
      fileName: cleanFileName
    };

    resultCard.style.display = 'flex';
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Copy Direct Link Button
  copyLinkBtn.addEventListener('click', () => {
    if (currentConversionData && currentConversionData.downloadUrl) {
      navigator.clipboard.writeText(currentConversionData.downloadUrl).then(() => {
        showToast('Lien direct copié dans le presse-papier !', 'success');
      });
    }
  });

  // Reset / Convert another
  resetBtn.addEventListener('click', () => {
    resultVideoPlayer.pause();
    resultAudioPlayer.pause();
    resultVideoPlayer.src = '';
    resultAudioPlayer.src = '';
    resultCard.style.display = 'none';
    urlInput.value = '';
    handleUrlChange('');
    urlInput.focus();
  });

  // Progress Bar Helper
  function updateProgress(percent, msg) {
    progressBar.style.width = `${percent}%`;
    statusPercent.textContent = `${percent}%`;
    statusMessage.textContent = msg;
  }

  function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Local Storage History
  function getHistory() {
    try {
      return JSON.parse(localStorage.getItem('flextube-history') || '[]');
    } catch {
      return [];
    }
  }

  function saveToHistory(item) {
    let history = getHistory();
    history.unshift(item);
    history = history.slice(0, 5);
    localStorage.setItem('flextube-history', JSON.stringify(history));
    renderHistory();
  }

  function renderHistory() {
    const history = getHistory();
    if (!history || history.length === 0) {
      historySection.style.display = 'none';
      return;
    }

    historySection.style.display = 'block';
    historyList.innerHTML = history.map(item => `
      <div class="history-item">
        <div class="history-item-left">
          <span class="history-badge">${item.platform}</span>
          <span class="history-title" title="${item.title}">${item.title}</span>
        </div>
        <div class="history-actions">
          <span class="chip chip-dim">${item.format}</span>
          <span class="chip chip-dim">${item.date}</span>
        </div>
      </div>
    `).join('');
  }

  clearHistoryBtn.addEventListener('click', () => {
    localStorage.removeItem('flextube-history');
    renderHistory();
    showToast('Historique effacé', 'info');
  });

  // Toast Notification System
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✓';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  // Initial load
  renderHistory();
});
