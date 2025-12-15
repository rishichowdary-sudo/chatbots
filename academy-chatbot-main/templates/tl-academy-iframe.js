"use client";
import { useEffect } from "react";
import styles from "./ChatbotIframe.module.css";

const IframeLoader = () => {
  useEffect(() => {
    const iframeContainer = document.getElementById("iframe-container");
    const iframeSrc = "https://academychat.terralogic.com/terralogic_academy";
    let chatbotOpened = false;

    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

    // Updated to include iPhone 16/16 Pro Max
    const isProMaxSize = () => {
      const width = window.screen.width;
      const height = window.screen.height;

      const knownProMaxHeights = [932];
      const knownProMaxWidths = [430];

      return (
        (knownProMaxWidths.includes(width) && knownProMaxHeights.includes(height)) ||
        (window.innerWidth <= 430 && window.innerHeight >= 852)
      );
    };

    const forcePreventZoom = () => {
      const metaViewport = document.querySelector('meta[name="viewport"]');
      if (metaViewport) {
        metaViewport.setAttribute(
          "content",
          "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"
        );
      }
      document.documentElement.style.zoom = 1;
    };

    const setupIframe = () => {
      let iframe = document.getElementById("chatbot-iframe");
      if (iframe) iframe.remove();

      iframe = document.createElement("iframe");
      iframe.id = "chatbot-iframe";
      iframe.src = isIOS ? `${iframeSrc}?preventzoom=true` : iframeSrc;
      iframe.className = styles.iframe;

      if (isIOS && isProMaxSize()) {
        iframe.style.height = "-webkit-fill-available";
      }

      iframe.onload = () => {
        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
          const style = document.createElement("style");
          style.textContent = `
            html, body {
              touch-action: manipulation;
              -webkit-text-size-adjust: none;
            }
            input, textarea, select {
              font-size: 16px !important;
              max-height: 999999px;
            }
          `;
          iframeDoc.head.appendChild(style);
        } catch (err) {
          console.log("Cross-origin: Cannot inject styles");
        }
      };

      iframeContainer.appendChild(iframe);
    };

    const expandChatbot = () => {
      const iframe = document.getElementById("chatbot-iframe");
      if (!iframe) return;

      iframe.style.transition = "none";
      void iframe.offsetWidth;

      if (isIOS && isProMaxSize()) {
        iframe.classList.add(styles.expandedIframe); // <-- Apply full-screen class
        iframeContainer.classList.add(styles.expanded);
      } else {
        iframe.style.width = "100vw";
        iframe.style.height = `${window.innerHeight}px`;
        iframe.style.maxWidth = "490px";
        iframe.style.maxHeight = "820px";
        iframe.style.borderRadius = "10px";
      }

      iframe.style.display = "block";
      if (window.innerWidth <= 768) {
        document.body.classList.add(styles.noScroll);
      }

      chatbotOpened = true;

      if (isIOS) {
        setTimeout(() => {
          window.scrollTo(0, 0);
          forcePreventZoom();
        }, 100);
      }
    };

    const collapseChatbot = () => {
      const iframe = document.getElementById("chatbot-iframe");
      if (!iframe) return;

      iframe.classList.remove(styles.expandedIframe);
      iframeContainer.classList.remove(styles.expanded);

      iframe.style.width = "120px";
      iframe.style.height = "120px";
      iframe.style.borderRadius = "10px";
      iframe.style.transition = "all 0.3s ease-in-out";
      iframe.style.display = "block";

      document.body.classList.remove(styles.noScroll);
      chatbotOpened = false;
    };

    const adjustIframeForOrientation = () => {
      if (chatbotOpened) {
        const iframe = document.getElementById("chatbot-iframe");
        if (iframe && isIOS && isProMaxSize()) {
          iframe.style.height = `${window.innerHeight}px`;
          setTimeout(() => {
            window.scrollTo(0, 0);
            forcePreventZoom();
          }, 100);
        }
      }
    };

    // Event listeners
    window.addEventListener("resize", adjustIframeForOrientation);
    window.addEventListener("orientationchange", adjustIframeForOrientation);

    document.addEventListener(
      "touchmove",
      (e) => {
        if (e.touches.length > 1) e.preventDefault();
      },
      { passive: false }
    );

    ["gesturestart", "gesturechange", "gestureend"].forEach((evt) => {
      document.addEventListener(
        evt,
        (e) => e.preventDefault(),
        { passive: false }
      );
    });

    if (isIOS) {
      setInterval(forcePreventZoom, 1000);
    }

    window.addEventListener("message", (event) => {
      const iframe = document.getElementById("chatbot-iframe");
      if (!iframe) return;

      switch (event.data.action) {
        case "expand":
          expandChatbot();
          break;
        case "collapse":
        case "collapseToast":
          collapseChatbot();
          break;
        case "expandToast":
          iframe.style.transition = "none";
          void iframe.offsetWidth;
          iframe.style.width = "100vw";
          iframe.style.maxWidth = "360px";
          iframe.style.height = "260px";
          iframe.style.maxHeight = "260px";
          iframe.style.borderRadius = "10px";
          iframe.style.display = "block";
          break;
        case "preventZoom":
          forcePreventZoom();
          break;
      }
    });

    setupIframe();
    adjustIframeForOrientation();
    forcePreventZoom();

    return () => {
      window.removeEventListener("resize", adjustIframeForOrientation);
      window.removeEventListener("orientationchange", adjustIframeForOrientation);
    };
  }, []);

  return <div id="iframe-container" className={styles.iframeContainer}></div>;
};

export default IframeLoader;