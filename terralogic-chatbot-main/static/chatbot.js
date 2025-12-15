// Chatbot Module
const ChatbotModule = (() => {

  // Constants
  const CONSTANTS = {
    MAX_MESSAGE_LENGTH: 400,
    MAX_INPUT_LENGTH: 500,
    SCROLL_SPEED_MULTIPLIER: 0.1,
    MAX_DELTA_TIME: 50,
    MAX_OPTIONS_DISPLAYED: 3,
    TYPING_DELAY: 1000,
    MAX_INPUT_HEIGHT: 100,
  };

  // DOMPurify config to remove tags. Currently, removes all HTML tags. 
  // Modify accordingly in case any HTML needs to be allowed.
  const configDomPurify = {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  };

  // DOM Element Cache
  const Elements = {
    init() {
      this.chatInput = document.querySelector(".chat-input textarea");
      this.sendButton = document.querySelector("#send-btn");
      this.chatBox = document.querySelector(".chatbox");
      this.chatToggle = document.querySelector(".chatbot-toggle");
      this.closeButton = document.querySelector("#chatbot-close-btn");
      this.optionsContainer = document.querySelector(".chat-options");
      this.chatPopup = document.querySelector(".toast");

      this.inputInitHeight = this.chatInput?.scrollHeight || 0;
    },
  };

  // State Management
  const State = {
    userMessage: "",
    sectionId: "",
    userSelectedOptions: [],
    botResponses: {},
    firstClick: true,
    currentOptions: [],

    save() {
      const state = {
        chatHistory: Elements.chatBox.innerHTML,
        userSelectedOptions: this.userSelectedOptions,
        botResponses: this.botResponses,
        firstClick: this.firstClick,
        sectionId: this.sectionId,
        currentOptions: this.currentOptions,
        optionsHTML: Elements.optionsContainer.innerHTML,
      };
      if (!this.sectionId) {
        this.sectionId = CookieManager.generateSectionId();
      }
      sessionStorage.setItem("chatbotSectionId", this.sectionId);
      sessionStorage.setItem("chatbotState", JSON.stringify(state));
      sessionStorage.setItem("chatbotSectionId", this.sectionId);
    },

    load() {
      const savedState = sessionStorage.getItem("chatbotState");
      const savedSectionId = sessionStorage.getItem("chatbotSectionId");
      if (savedSectionId) {
        this.sectionId = savedSectionId;
      }
      const savedJobContainer = sessionStorage.getItem("jobContainerHTML");


      if (!savedState && !savedSectionId) return false;

      if (savedState) {
        const state = JSON.parse(savedState);
        Elements.chatBox.innerHTML = state.chatHistory || "";

        const wasLastJobContainer = sessionStorage.getItem("jobContainerIsLast") === "true";

        if (savedJobContainer && wasLastJobContainer) {
          const jobContainer = document.createElement("div");
          jobContainer.innerHTML = savedJobContainer;
          Elements.chatBox.appendChild(jobContainer.firstChild);
        }


        this.userSelectedOptions = state.userSelectedOptions;
        this.botResponses = state.botResponses;
        this.firstClick = state.firstClick;
        this.currentOptions = state.currentOptions || [];
        Elements.optionsContainer.innerHTML = state.optionsHTML || "";
        if (this.currentOptions.length > 0) {
          ChatHandler.showOptions(this.currentOptions.map(opt => opt.text));
        }

        // Process all messages to ensure visibility
        document.querySelectorAll(".chat.incoming .message-content").forEach((content) => {
          const fullMessage = content.getAttribute("data-full-message");
          if (fullMessage) {
            const newContent = document.createElement("p");
            newContent.classList.add("message-content");
            newContent.setAttribute("data-message-id", content.getAttribute("data-message-id"));
            newContent.setAttribute("data-full-message", fullMessage);

            const truncatedMessage = content.getAttribute("data-truncated-message");
            if (truncatedMessage) {
              newContent.setAttribute("data-truncated-message", truncatedMessage);
            }

            // Inject stripped HTML
            const safeHTML = UIComponents.stripBlockElements(fullMessage);
            newContent.innerHTML = safeHTML;
            newContent.style.visibility = "visible";
            newContent.style.opacity = "1";

            content.parentNode.replaceChild(newContent, content);
          }
        });

        // Reattach all interactive elements
        this.reattachEventListeners();
        UIComponents.reattachMessageHandlers?.();
        UIComponents.reattachLinkIcons(Elements.chatBox);
        ChatHandler.reattachChatMessageOptions();
        ChatHandler.checkForActiveOptions();

        // Ensure proper scroll position
        Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);

        return true;
      }

      return false;
    },

    reattachEventListeners() {
      // Reattach listeners to all option buttons
      const allOptionButtons = document.querySelectorAll(
        ".chat-bot-message-options .option-button, .chat-message-options .option-button"
      );

      allOptionButtons.forEach((button) => {
        // Remove existing click handlers
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);

        // Get the option text and type
        const optionText = newButton.getAttribute("data-option");
        const optionType = newButton.getAttribute("data-option-type");

        if (optionText) {
          newButton.onclick = () => ChatHandler.handleOptionClick(optionText);

          // Ensure proper styling based on option type
          if (optionType === "chat-message") {
            newButton
              .closest(".chat-message-options")
              ?.classList.add("chat-message-options");
          } else {
            newButton
              .closest(".chat-bot-message-options")
              ?.classList.add("chat-bot-message-options");
          }
        }
      });

      // Reattach show more/less button handlers
      const showMoreButtons =
        Elements.chatBox.querySelectorAll(".show-more-btn");
      showMoreButtons.forEach((button) => {
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);

        newButton.onclick = () => {
          const content = newButton.parentElement;
          const fullMessage = content.getAttribute("data-full-message");
          const truncatedMessage = content.getAttribute(
            "data-truncated-message"
          );
          const isTruncated = newButton.textContent === "Show More";

          if (isTruncated) {
            newButton.textContent = "Show Less";
            content.innerHTML = UIComponents.stripBlockElements(fullMessage);
          } else {
            newButton.textContent = "Show More";
            content.innerHTML =
              UIComponents.stripBlockElements(truncatedMessage);
          }
          content.appendChild(newButton);
        };
      });

      const faqButtons = document.querySelectorAll('.faq-button');
      faqButtons.forEach(button => {
        // Remove existing click handlers
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);

        newButton.addEventListener('click', () => {
          const optionsContainer = newButton.parentElement.querySelector('.chat-bot-message-options');
          const arrow = newButton.querySelector('.faq-arrow');
          const isExpanded = optionsContainer.style.display === 'block';

          if (isExpanded) {
            optionsContainer.style.opacity = '0';
            arrow.style.transform = 'rotate(0deg)';
            newButton.classList.remove('active');
            setTimeout(() => {
              optionsContainer.style.display = 'none';
            }, 300);
          } else {
            optionsContainer.style.display = 'block';
            arrow.style.transform = 'rotate(180deg)';
            newButton.classList.add('active');
            setTimeout(() => {
              optionsContainer.style.opacity = '1';
            }, 10);
          }
        });
      });

      // Also ensure options containers are in correct initial state
      const optionsContainers = document.querySelectorAll('.chat-bot-message-options');
      optionsContainers.forEach(container => {
        container.style.display = 'none';
        container.style.opacity = '0';
      });

      const allLinks = Elements.chatBox.querySelectorAll("a");
      allLinks.forEach(link => {
        // Remove any existing icons
        const existingIcons = link.querySelectorAll("img");
        existingIcons.forEach(icon => icon.remove());

        // Set up link styling
        link.style.display = "inline-flex";
        link.style.alignItems = "center";
        link.style.gap = "5px";

        // Create and append new icon
        const arrowIcon = document.createElement("img");
        arrowIcon.src = "/static/assets/icons/arrow_up_right.svg";
        arrowIcon.alt = "External Link";
        arrowIcon.style.width = "16px";
        arrowIcon.style.height = "16px";
        arrowIcon.style.filter = "invert(20%) sepia(95%) saturate(7476%) hue-rotate(233deg) brightness(102%) contrast(101%)";

        link.appendChild(arrowIcon);
      });
    },

    clear() {
      sessionStorage.removeItem("chatbotState");
      sessionStorage.removeItem("chatbotSectionId");
      sessionStorage.removeItem("chatbotRestored"); // Ensure restored messages are cleared
      sessionStorage.removeItem("jobContainerHTML");
      sessionStorage.removeItem("jobContainerIsLast");
      Elements.chatBox.innerHTML = "";
      this.userSelectedOptions = [];
      this.botResponses = {};
      this.firstClick = true;
      this.currentOptions = [];
      this.sectionId = CookieManager.generateSectionId();
      this.save();
      Elements.optionsContainer.innerHTML = "";
      Elements.chatInput.disabled = false;
      Elements.chatInput.placeholder = "Write your message...";
    }
  };

  // Cookie Management
  const CookieManager = {
    set(name, value) {
      document.cookie = `${name}=${value};path=/`;
    },

    get(name) {
      const cookieArr = document.cookie.split(";");
      for (let cookie of cookieArr) {
        const [cookieName, cookieValue] = cookie
          .split("=")
          .map((c) => c.trim());
        if (cookieName === name) return cookieValue;
      }
      return null;
    },

    generateSectionId() {
      return "section-" + Math.random().toString(36).substr(2, 9);
    },
  };
  let typingDone = false;
  // UI Components
  const UIComponents = {

    createTimeStamp(alignment) {
      const date = new Date();
      const day = String(date.getDate()).padStart(2, "0");
      const month = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ][date.getMonth()];
      const time = `${String(date.getHours()).padStart(2, "0")}:${String(
        date.getMinutes()
      ).padStart(2, "0")}`;

      const chatLi = document.createElement("li");
      chatLi.classList.add("chat-time", `${alignment}-time`);

      const timeContent =
        alignment === "center" ? `${day} ${month} ${time}` : time;

      chatLi.innerHTML = `<p>${timeContent}</p>`;
      return chatLi;
    },

    createChatMessage(message, className) {
      const chatLi = document.createElement("li");
      chatLi.classList.add("chat", className);

      if (Array.isArray(message)) {
        return this.createJobTiles(message, chatLi);
      }

      if (className === "incoming") {
        // Create wrapper for logo and message
        const messageWrapper = document.createElement("div");
        messageWrapper.classList.add("message-wrapper");

        // Create logo container
        const logoContainer = document.createElement("div");
        logoContainer.classList.add("bot-logo");

        // Add logo image
        const logoImg = document.createElement("img");
        logoImg.src = "/static/assets/icons/logo.svg";
        logoImg.alt = "Chatbot Logo";
        logoImg.classList.add("bot-logo-img");

        // Assemble the message
        logoContainer.appendChild(logoImg);
        messageWrapper.appendChild(logoContainer);

        // Create the message content using existing method
        const messageContent = this.createTextMessage(message, chatLi, true); // Pass 'true' for incoming
        if (messageContent.tagName?.toLowerCase() === "p") {
          messageWrapper.appendChild(messageContent);
        } else {
          messageWrapper.appendChild(messageContent.querySelector("p"));
        }

        chatLi.appendChild(messageWrapper);
        return chatLi;
      }

      // Outgoing messages should appear instantly
      this.createTextMessage(message, chatLi, false);
      return chatLi;
    },

    createJobTiles(jobs, container) {
      // Create main tile container
      const tileContainer = document.createElement("div");
      tileContainer.classList.add("tile-container");

      // Create a single tile to hold all job details
      const singleTile = document.createElement("div");
      singleTile.classList.add("tile", "single-tile");

      // Add all jobs' details inside the single tile
      jobs.forEach((job) => {
        const jobElement = this.createJobTile(job);
        singleTile.appendChild(jobElement);
      });
      tileContainer.appendChild(singleTile);
      container.appendChild(tileContainer);
      sessionStorage.setItem("jobContainerHTML", tileContainer.outerHTML);
      sessionStorage.setItem("jobContainerIsLast", "true");

      setTimeout(() => {
        Elements.chatBox.appendChild(UIComponents.createTimeStamp("incoming"));
        Elements.chatBox.scrollTo({
          top: Elements.chatBox.scrollHeight,
          behavior: 'smooth'
        });
      }, 300);

      return container;
    },

    createJobTile(jobData) {
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = jobData;

      const title =
        tempDiv
          .querySelector("b:nth-of-type(1)")
          ?.nextSibling?.textContent.trim() || "No Title";
      const location =
        tempDiv
          .querySelector("b:nth-of-type(2)")
          ?.nextSibling?.textContent.trim() || "No Location";
      const applyLink = tempDiv.querySelector("a")?.href || "#";

      // Create job entry
      const jobEntry = document.createElement("div");
      jobEntry.classList.add("job-entry");

      const jobLeftsection = document.createElement("div");
      jobLeftsection.classList.add("job-left");
      // Job title (on top)
      const jobTitle = document.createElement("div");
      jobTitle.classList.add("job-title");
      jobTitle.innerHTML = `${title.replace(":", "")}`;

      // Job content (location + button in the same row)
      const jobContent = document.createElement("div");
      jobContent.classList.add("job-content");

      const jobInfo = document.createElement("div");
      jobInfo.classList.add("job-info");
      jobInfo.innerHTML = `${location
        .replace(":", "")
        .replaceAll(",", "<strong>|</strong>")}`;

      const applyButton = document.createElement("a");
      applyButton.classList.add("tile-link");
      applyButton.href = applyLink;
      applyButton.target = "_parent"; 
      applyButton.rel = "noopener noreferrer";
      applyButton.textContent = "";

      // Append elements
      jobLeftsection.appendChild(jobTitle);
      jobLeftsection.appendChild(jobInfo);
      jobContent.appendChild(applyButton);

      jobEntry.appendChild(jobLeftsection);
      jobEntry.appendChild(jobContent);

      return jobEntry;
    },

    createTextMessage(message, container, isIncoming = false) {
      typingDone = false
      const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const isTruncated = message.length > CONSTANTS.MAX_MESSAGE_LENGTH;

      const content = document.createElement("p");
      content.classList.add("message-content");
      content.setAttribute("data-message-id", messageId);
      content.setAttribute("data-full-message", message);
      content.id = 'message-content'

      const expandedState = sessionStorage.getItem(`expanded_${messageId}`);
      const isExpanded = expandedState === "true";

      let displayMessage = message;
      if (isTruncated && !isExpanded) {
        displayMessage = message.slice(0, CONSTANTS.MAX_MESSAGE_LENGTH) + "...";
        content.setAttribute("data-truncated-message", displayMessage);
      }
      // Strip outer <p> tags if present in the raw message
      if (displayMessage.trim().startsWith("<p>") && displayMessage.trim().endsWith("</p>")) {
        displayMessage = displayMessage.trim().slice(3, -4).trim();
      }


      // Retrieve restored messages
      let restoredMessages = JSON.parse(sessionStorage.getItem("chatbotRestored") || "[]");

      // Ensure message content is immediately visible for restored messages
      const messageKey = `${messageId}_${message}`;
      if (restoredMessages.includes(messageKey)) {
        let cleanMessage = displayMessage.trim();

        // Remove outer <p>...</p> if present
        if (cleanMessage.startsWith("<p>") && cleanMessage.endsWith("</p>")) {
          cleanMessage = cleanMessage.slice(3, -4).trim();
        }

        content.innerHTML = this.stripBlockElements(cleanMessage);

        // content.innerHTML = safeHTML;
        if (isTruncated) {
          this.addShowMoreButton(content, message, messageId);
        }
        UIComponents.reattachLinkIcons(content);
        return container;
      }

      // Apply typewriter effect only for new incoming messages
      if (isIncoming && !restoredMessages.includes(message)) {
        const span = document.createElement("span");
        span.style.visibility = "visible";
        content.appendChild(span);

        let index = 0;

        const typingInterval = setInterval(() => {
          span.style.visibility = "visible";
          content.innerHTML = this.stripBlockElements(displayMessage.slice(0, index + 1));

          // Smooth scroll during typing
          const chatBox = document.querySelector(".chatbox");
          const scrollTarget = chatBox.scrollHeight - chatBox.clientHeight;

          // Use smooth scrolling
          chatBox.scrollTo({
            top: scrollTarget,
            behavior: 'smooth'
          });

          index++;
          if (index === displayMessage.length) {
            clearInterval(typingInterval);
            typingDone = false
            setTimeout(() => {
              typingDone = true;
              if (isTruncated) {
                this.addShowMoreButton(content, message, messageId);
              }
              UIComponents.reattachLinkIcons(content);
              // Final scroll after message is complete
              chatBox.scrollTo({
                top: chatBox.scrollHeight,
                behavior: 'smooth'
              });
            }, 500);
          }
        }, 20);

      } else {
        content.innerHTML = this.stripBlockElements(displayMessage);
        if (isTruncated) {
          this.addShowMoreButton(content, message, messageId);

        }
      }

      // Save restored messages
      if (isIncoming && !restoredMessages.includes(message)) {
        restoredMessages.push(messageKey);
        sessionStorage.setItem("chatbotRestored", JSON.stringify(restoredMessages));
      }

      container.appendChild(content);

      sessionStorage.setItem("jobContainerIsLast", "false");

      return container;
    },

    addShowMoreButton(content, message, messageId) {
      const showMoreBtn = document.createElement("button");
      showMoreBtn.textContent = "Show More";
      showMoreBtn.classList.add("show-more-btn");

      showMoreBtn.addEventListener("click", () => {
        const isExpanded = showMoreBtn.textContent === "Show Less";
        if (isExpanded) {
          content.innerHTML = this.stripBlockElements(
            message.slice(0, CONSTANTS.MAX_MESSAGE_LENGTH) + "..."
          );
          showMoreBtn.textContent = "Show More";
          sessionStorage.setItem(`expanded_${messageId}`, "false");
        } else {
          content.innerHTML = this.stripBlockElements(message);
          showMoreBtn.textContent = "Show Less";
          sessionStorage.setItem(`expanded_${messageId}`, "true");

          setTimeout(() => {
            const chatBox = Elements.chatBox;
            const messageBottom = content.getBoundingClientRect().bottom;
            const chatBoxBottom = chatBox.getBoundingClientRect().bottom;

            if (messageBottom > chatBoxBottom) {
              chatBox.scrollTo({
                top: chatBox.scrollTop + (messageBottom - chatBoxBottom) + 50,
                behavior: "smooth"
              });
            }
          }, 100);
        }
        UIComponents.reattachLinkIcons(content);
        content.appendChild(showMoreBtn);
      });

      content.appendChild(showMoreBtn);
    },

    stripBlockElements(message) {
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = message;

      if (
        tempDiv.childNodes.length === 1 &&
        tempDiv.firstChild.tagName === "P"
      ) {
        tempDiv.innerHTML = tempDiv.firstChild.innerHTML;
      }

      // Special handling for h2 tags - wrap content in strong tags
      const h2Elements = tempDiv.querySelectorAll("h2");
      h2Elements.forEach((h2) => {
        const content = h2.innerHTML;
        h2.innerHTML = `<strong>${content}</strong>`;
      });

      // Process nested lists first (innermost ul elements)
      let ulElements = tempDiv.querySelectorAll("ul");
      while (ulElements.length > 0) {
        ulElements.forEach((ul) => {
          const listItems = ul.querySelectorAll("li");
          let listContent = "<br>"; // Add line break before the list

          listItems.forEach((li, index) => {
            listContent += `• ${li.innerHTML}`;
            if (index < listItems.length - 1) {
              listContent += "<br>";
            }
          });

          listContent += "<br>"; // Add line break after the list

          const replacement = document.createElement("span");
          replacement.innerHTML = listContent;
          ul.replaceWith(replacement);
        });
        // Check for any remaining ul elements after replacement
        ulElements = tempDiv.querySelectorAll("ul");
      }

      // Process ol elements after ul elements are handled
      let olElements = tempDiv.querySelectorAll("ol");
      while (olElements.length > 0) {
        olElements.forEach((ol) => {
          const listItems = ol.querySelectorAll("li");
          let listContent = "<br>"; // Add line break before the list

          listItems.forEach((li, index) => {
            let liContent = li.innerHTML.trim();

            // Clean up nested p tags within li elements to reduce excessive spacing
            liContent = liContent.replace(/<p>/g, '').replace(/<\/p>/g, '<br>');
            // Remove multiple consecutive br tags
            liContent = liContent.replace(/(<br\s*\/?>){2,}/g, '<br>');
            // Remove trailing br tags
            liContent = liContent.replace(/(<br\s*\/?>)+$/g, '');

            if (liContent.includes('<br>')) {
              liContent = liContent.replace(/<br>/g, '<br>  ');
            }

            listContent += `<strong>${index + 1}.</strong> ${liContent}`;
            if (index < listItems.length - 1) {
              listContent += "<br><br>";
            }
          });

          listContent += "<br>"; // Reduced line breaks after the list

          const replacement = document.createElement("span");
          replacement.innerHTML = listContent;
          ol.replaceWith(replacement);
        });
        // Check for any remaining ol elements after replacement
        olElements = tempDiv.querySelectorAll("ol");
      }

      // Handle any remaining standalone li elements
      const standaloneliElements = tempDiv.querySelectorAll("li");
      standaloneliElements.forEach((li) => {
        const replacement = document.createElement("span");
        replacement.innerHTML = `${li.innerHTML}<br>`;
        li.replaceWith(replacement);
      });

      // Handle p elements - convert to spans with line breaks for separation
      const pElements = tempDiv.querySelectorAll("p");
      pElements.forEach((p, index) => {
        const replacement = document.createElement("span");
        replacement.innerHTML = p.innerHTML;
        // Only add double line break if it's not the last p element
        const isLastP = index === pElements.length - 1;
        replacement.innerHTML += isLastP ? "<br>" : "<br><br>";

        p.replaceWith(replacement);
      });

      // Handle div elements - add line break before content (except for the first element)
      const divElements = tempDiv.querySelectorAll("div");
      divElements.forEach((div, index) => {
        const replacement = document.createElement("span");
        // Don't add line break before the first div if it's the first child
        const isFirstElement = div === tempDiv.firstElementChild;
        replacement.innerHTML = (isFirstElement ? "" : "<br>") + div.innerHTML;
        div.replaceWith(replacement);
      });

      // Handle other block elements
      const blockElements = [
        "h1",
        "h3",
        "h4",
        "h5",
        "h6"
      ];

      blockElements.forEach((tag) => {
        const elements = tempDiv.querySelectorAll(tag);
        elements.forEach((el) => {
          el.replaceWith(...el.childNodes);
        });
      });

      // Handle h2 elements after other processing
      const h2ElementsAfter = tempDiv.querySelectorAll("h2");
      h2ElementsAfter.forEach((h2) => {
        const strongContent = h2.querySelector("strong")?.innerHTML || h2.innerHTML;
        const strongElement = document.createElement("strong");
        strongElement.style.fontSize = "18px";
        strongElement.textContent = strongContent;
        h2.replaceWith(strongElement);
      });

      // Clean up extra line breaks at the end and beginning
      let result = tempDiv.innerHTML;
      result = result.replace(/(<br\s*\/?>){4,}/g, '<br><br>'); // Replace 4+ consecutive breaks with 2
      result = result.replace(/(<br\s*\/?>){3}/g, '<br><br>'); // Replace 3 consecutive breaks with 2
      result = result.replace(/^(<br\s*\/?>)+/g, ''); // Remove line breaks at the beginning
      result = result.replace(/(<br\s*\/?>)+$/g, ''); // Remove line breaks at the end

      return result;
    },
    reattachMessageHandlers() {
      const messages = document.querySelectorAll(".message-content");

      messages.forEach((content) => {
        const messageId = content.getAttribute("data-message-id");
        const fullMessage = content.getAttribute("data-full-message");
        const truncatedMessage = content.getAttribute("data-truncated-message");

        if (!messageId || !fullMessage || !truncatedMessage) return;

        // Remove any existing show more button to prevent duplication
        const existingBtn = content.querySelector(".show-more-btn");
        if (existingBtn) {
          existingBtn.remove();
        }

        // Create new button with proper state
        const expandedState = sessionStorage.getItem(`expanded_${messageId}`);
        const isExpanded = expandedState === "true";

        const showMoreBtn = document.createElement("button");
        showMoreBtn.textContent = isExpanded ? "Show Less" : "Show More";
        showMoreBtn.classList.add("show-more-btn");

        showMoreBtn.addEventListener("click", () => {
          const currentlyExpanded = showMoreBtn.textContent === "Show Less";

          if (currentlyExpanded) {
            // Show truncated version
            content.innerHTML = this.stripBlockElements(truncatedMessage);
            showMoreBtn.textContent = "Show More";
            sessionStorage.setItem(`expanded_${messageId}`, "false");
          } else {
            // Show full version
            content.innerHTML = this.stripBlockElements(fullMessage);
            showMoreBtn.textContent = "Show Less";
            sessionStorage.setItem(`expanded_${messageId}`, "true");
          }

          // Reattach link icons after modifying content
          this.reattachLinkIcons(content);

          // Reattach the button
          content.appendChild(showMoreBtn);
        });

        // Set initial content state
        content.innerHTML = isExpanded
          ? this.stripBlockElements(fullMessage)
          : this.stripBlockElements(truncatedMessage);

        // Reattach link icons for initial state
        this.reattachLinkIcons(content);

        // Add the button
        content.appendChild(showMoreBtn);
      });
    },

    // Add new helper method for link icon reattachment
    reattachLinkIcons(container) {
      const links = container.querySelectorAll("a");
      links.forEach((link) => {
        if (link.classList.contains("tile-link")) {
          const existingIcons = link.querySelectorAll("img");
          existingIcons.forEach((icon) => icon.remove());

          // Optional: remove style if added
          link.style.display = '';
          link.style.alignItems = '';
          link.style.gap = '';
          return;
        }
        // Remove any existing icons first
        const existingIcons = link.querySelectorAll("img");
        existingIcons.forEach((icon) => icon.remove());

        // Set up link styling
        link.style.display = "inline-flex";
        link.style.alignItems = "center";
        link.style.gap = "5px";

        // Create and append new icon
        const arrowIcon = document.createElement("img");
        arrowIcon.src = "/static/assets/icons/arrow_up_right.svg";
        arrowIcon.alt = "External Link";
        arrowIcon.style.width = "16px";
        arrowIcon.style.height = "16px";
        arrowIcon.style.filter = "invert(20%) sepia(95%) saturate(7476%) hue-rotate(233deg) brightness(102%) contrast(101%)";
        link.appendChild(arrowIcon);
      });
    },

    createMenu() {
      const menuContainer = document.createElement("div");
      menuContainer.className = "chatbot-menu";

      const menuButton = document.createElement("button");
      menuButton.className = "menu-toggle";

      const menuIcon = document.createElement("img");
      menuIcon.src = "/static/assets/icons/menu.svg";
      menuIcon.alt = "menu";
      menuButton.appendChild(menuIcon);

      // Create overlay
      const menuOverlay = document.createElement("div");
      menuOverlay.className = "menu-overlay";

      // Create menu dropdown inside overlay
      const menuDropdown = document.createElement("div");
      menuDropdown.className = "menu-dropdown";
      menuDropdown.innerHTML = `
      <button class="menu-item" data-action="start-project"><span>Start a project</span></button>
      <button class="menu-item" data-action="career"><span>Looking for a job</span></button>
      <button class="menu-item" data-action="explore"><span>Explore services</span></button>
    `;

      // Append dropdown inside overlay
      menuOverlay.appendChild(menuDropdown);
      menuContainer.appendChild(menuButton);
      menuContainer.appendChild(menuOverlay);

      return menuContainer;
    },

    createTypingAnimation() {
      const typingContainer = document.createElement("li");
      typingContainer.classList.add("chat", "incoming");

      // Create wrapper for logo and typing indicator
      const messageWrapper = document.createElement("div");
      messageWrapper.classList.add("message-wrapper");

      // Create and add logo container
      const logoContainer = document.createElement("div");
      logoContainer.classList.add("bot-logo");

      // Add SVG logo
      const logoImg = document.createElement("img");
      logoImg.src = "/static/assets/icons/logo.svg";
      logoImg.alt = "Chatbot Logo";
      logoImg.classList.add("bot-logo-img");

      logoContainer.appendChild(logoImg);
      messageWrapper.appendChild(logoContainer);

      // Create typing indicator
      const indicator = document.createElement("div");
      indicator.classList.add("typing-indicator");
      indicator.textContent = "Just wait a second..";
      // indicator.innerHTML = '<span class="dot"></span>'.repeat(3);

      messageWrapper.appendChild(indicator);
      typingContainer.appendChild(messageWrapper);

      return typingContainer;
    },
  };

  // Add Tab Visibility Handler
  const TabVisibilityHandler = {
    init() {
      // Handle tab close or navigation away
      window.addEventListener("beforeunload", () => {
        // Update last active timestamp before unload
        const currentState = sessionStorage.getItem("chatbotState");
        if (currentState) {
          const state = JSON.parse(currentState);
          state.lastActive = Date.now();
          sessionStorage.setItem("chatbotState", JSON.stringify(state));
        }
      });

      // Handle tab visibility change
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "hidden") {
          // Update last active timestamp when tab becomes hidden
          const currentState = sessionStorage.getItem("chatbotState");
          if (currentState) {
            const state = JSON.parse(currentState);
            state.lastActive = Date.now();
            sessionStorage.setItem("chatbotState", JSON.stringify(state));
          }
        } else {
          // Check if we need to clear state when tab becomes visible
          this.checkStateValidity();
        }
      });
    },

    checkStateValidity() {
      const currentState = sessionStorage.getItem("chatbotState");
      if (!currentState) return;

      const state = JSON.parse(currentState);
      const currentTime = Date.now();
      const timeDifference = currentTime - state.lastActive;

      // Clear both state and sectionId if tab was closed (inactive for more than 1 minute)
      if (timeDifference > 3600000) {
        State.clear();
        // Generate new sectionId for the new session
        State.sectionId = CookieManager.generateSectionId();
        State.save();
      }
    },
  };

  // Chat Handler
  const ChatHandler = {
    async handleChat() {
      const userInput = Elements.chatInput.value.trim();
      // console.log("before cleanup: ", userInput);
      const cleanUserInput = DOMPurify.sanitize(userInput, configDomPurify);
      // console.log("after cleanup: ", cleanUserInput);
      if (!cleanUserInput) return;

      // Reset input
      Elements.chatInput.value = "";
      Elements.chatInput.style.height = "20px";
      Elements.chatInput.style.overflowY = "hidden";

      // Add user message to chat
      Elements.chatBox.appendChild(
        UIComponents.createChatMessage(cleanUserInput, "outgoing")
      );
      Elements.chatBox.appendChild(UIComponents.createTimeStamp("outgoing"));
      State.userSelectedOptions.push(cleanUserInput.toLowerCase());
      Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);

      // Get and display bot response
      await this.fetchBotResponses(cleanUserInput.toLowerCase());
      await this.handleBotReply(cleanUserInput.toLowerCase());
      State.save();
    },

    async fetchBotResponses(userText) {
      const typingIndicator = UIComponents.createTypingAnimation();
      Elements.chatBox.appendChild(typingIndicator);
      Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);

      try {
        const response = await fetch(
          "/getresponses",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Cache-Control": "no-cache",
            },
            body: JSON.stringify({
              user_input: userText,
              client_id: clientId,
              session_id: State.sectionId,
            }),
          }
        );

        if (!response.ok) throw new Error("Failed to fetch responses");
        State.botResponses = {
          ...State.botResponses,
          ...(await response.json()),
        };
      } catch (error) {
        console.error("Error fetching bot responses:", error);
      } finally {
        typingIndicator.remove();
      }
    },

    async handleBotReply(userText) {
      const typingIndicator = UIComponents.createTypingAnimation();
      Elements.chatBox.appendChild(typingIndicator);

      // Scroll to show typing indicator
      Elements.chatBox.scrollTo({
        top: Elements.chatBox.scrollHeight,
        behavior: 'smooth'
      });

      return new Promise((resolve) => {
        setTimeout(() => {
          const botResponse = State.botResponses[userText];
          typingIndicator.remove();

          if (botResponse) {
            Elements.chatBox.appendChild(
              UIComponents.createChatMessage(botResponse.response, "incoming")
            );

            if (botResponse.jobs?.length > 0) {
              setTimeout(() => {
                Elements.chatBox.appendChild(
                  UIComponents.createChatMessage(botResponse.jobs, "incoming")
                );
              }, CONSTANTS.TYPING_DELAY * 4)
            }
            Elements.chatBox.appendChild(
              UIComponents.createTimeStamp("incoming")
            );
            Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);

            // Show standard options after initial delay
            // console.log(botResponse.response)
            // console.log(typingDone, 'typingDone')
            const checkTypingDoneInterval = setInterval(() => {
              if (typingDone && botResponse.options?.length > 0) {
                // console.log('this is executed');
                this.showOptions(botResponse.options);
                typingDone = false; // Reset typingDone flag
                clearInterval(checkTypingDoneInterval);
              }
            }, 100);



            // Show chat message options after a longer delay
            if (botResponse.chatMessageOptions?.length > 0) {
              setTimeout(() => {
                this.showChatMessageOptions(botResponse.chatMessageOptions);
              }, CONSTANTS.TYPING_DELAY * 4);
            }
          } else {
            Elements.chatBox.appendChild(
              UIComponents.createChatMessage(
                "We're experiencing a brief hiccup! 🌟 Our servers are taking a quick breather, but your creativity inspires us. Please check back in a few minutes - we'd love to continue this journey together. ✨",
                "incoming"
              )
            );
            Elements.chatBox.appendChild(UIComponents.createTimeStamp("incoming"));
          }

          // Final scroll to bottom
          Elements.chatBox.scrollTo({
            top: Elements.chatBox.scrollHeight,
            behavior: 'smooth'
          });

          State.save();
          resolve();
        }, CONSTANTS.TYPING_DELAY);
      });
    },
    checkForActiveOptions() {
      const hasOptions = Elements.chatBox.querySelector(
        ".chat-message-options"
      );
      Elements.chatInput.disabled = !!hasOptions;
      Elements.chatInput.placeholder = hasOptions
        ? "Please select an option above..."
        : "Write your message...";
    },

    handleOptionClick(option) {
      const menuOverlay = document.querySelector(".menu-overlay");
      const menuDropdown = document.querySelector(".menu-dropdown");

      if (menuOverlay) {
        menuOverlay.classList.remove("show");
      }
      if (menuDropdown) {
        menuDropdown.classList.remove("show");
      }

      // console.log("Option selected:", option);

      // Prevent duplicate selections
      if (!State.userSelectedOptions.includes(option.toLowerCase())) {
        State.userSelectedOptions.push(option.toLowerCase());
      }

      // Remove options UI from chat
      const chatMessageOptionsElements = Elements.chatBox.querySelectorAll(
        ".chat.incoming .chat-message-options"
      );
      const animationPromises = [];

      chatMessageOptionsElements.forEach((element) => {
        // Find the parent li element that contains both the options and timestamp
        const parentLi = element.closest("li.chat.incoming");
        const nextTimestamp = parentLi?.nextElementSibling;

        if (parentLi && nextTimestamp) {
          // Add fadeout animation
          parentLi.style.overflow = "hidden";
          parentLi.classList.add("animate-fadeOutDown");
          nextTimestamp.classList.add("animate-fadeOutDown");

          // Create a promise to remove elements after animation
          const animationPromise = new Promise((resolve) => {
            parentLi.addEventListener(
              "animationend",
              () => {
                parentLi.remove();
                nextTimestamp.remove();
                resolve();
              },
              { once: true }
            );
          });

          animationPromises.push(animationPromise);
        }
      });

      // Wait for animations to complete
      Promise.all(animationPromises).then(() => {
        // Ensure the FAQ container is also removed
        const existingFAQs = Elements.chatBox.querySelectorAll('.faq-container');
        existingFAQs.forEach(faq => faq.remove());

        // Ensure chat input is re-enabled after options are removed
        this.checkForActiveOptions();

        // Display user-selected option in chat
        Elements.chatBox.appendChild(UIComponents.createChatMessage(option, "outgoing"));
        Elements.chatBox.appendChild(UIComponents.createTimeStamp("outgoing"));
        Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);
        Elements.optionsContainer.innerHTML = "";

        // Fetch and display bot response
        this.fetchBotResponses(option.toLowerCase())
          .then(() => this.handleBotReply(option.toLowerCase()))
          .then(() => {
            // Save state after processing response
            State.save();
            Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);
          });
      });
    },

    showOptions(chatMessageOptions) {
      const existingFAQs = Elements.chatBox.querySelectorAll('.faq-container');
      existingFAQs.forEach(faq => faq.remove());

      const filteredOptions = [...new Set(chatMessageOptions)]
        .filter(option => !State.userSelectedOptions.includes(option.toLowerCase()))
        .slice(0, 3);

      if (filteredOptions.length === 0) {
        return;
      }

      const faqMessageLi = document.createElement('li');
      faqMessageLi.className = 'chat incoming faq-container';

      const faqButtonContainer = document.createElement('div');
      faqButtonContainer.className = 'faq-button-container';

      // Create options container
      const chatMessageOptionsContainer = document.createElement('div');
      chatMessageOptionsContainer.className = 'chat-bot-message-options';
      chatMessageOptionsContainer.style.display = 'none';
      chatMessageOptionsContainer.style.opacity = '0';

      const optionsContainer = document.createElement('div');
      optionsContainer.className = 'options-container';

      // Populate only 3 unique options dynamically
      filteredOptions.forEach(option => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'option';
        optionDiv.textContent = option;
        optionDiv.setAttribute("data-option", option);
        optionDiv.setAttribute("data-option-type", "standard");

        const optionIcon = document.createElement("img");
        optionIcon.src = "/static/assets/icons/arrow-right.svg";
        optionIcon.alt = "Option Icon";
        optionIcon.className = "option-icon";

        optionDiv.appendChild(optionIcon);
        optionDiv.onclick = () => this.handleOptionClick(option);
        optionsContainer.appendChild(optionDiv);
      });

      // Add options to container
      chatMessageOptionsContainer.appendChild(optionsContainer);

      // Create FAQ toggle button
      const faqButton = document.createElement('button');
      faqButton.className = 'faq-button';
      faqButton.innerHTML = `
        <span>Got questions? Check our FAQ's</span>
        <img src="/static/assets/icons/Chevron_Down.svg" alt="Expand FAQ" class="faq-arrow" />
    `;

      faqButton.addEventListener('click', () => {
        const arrow = faqButton.querySelector('.faq-arrow');
        const isExpanded = chatMessageOptionsContainer.style.display === 'block';

        if (isExpanded) {
          chatMessageOptionsContainer.style.opacity = '0';
          arrow.style.transform = 'rotate(0deg)';
          faqButton.classList.remove('active');
          setTimeout(() => {
            chatMessageOptionsContainer.style.display = 'none';
          }, 300);
        } else {
          chatMessageOptionsContainer.style.display = 'block';
          arrow.style.transform = 'rotate(180deg)';
          faqButton.classList.add('active');
          setTimeout(() => {
            chatMessageOptionsContainer.style.opacity = '1';
            Elements.chatBox.scrollTo({
              top: Elements.chatBox.scrollHeight,
              behavior: 'smooth'
            });
          }, 10);
        }
        sessionStorage.setItem("jobContainerIsLast", "false");
      });

      // Append FAQ components
      faqButtonContainer.appendChild(chatMessageOptionsContainer);
      faqButtonContainer.appendChild(faqButton);
      faqMessageLi.appendChild(faqButtonContainer);

      // Insert FAQ message before the last incoming timestamp
      const lastIncomingTimestamp = Elements.chatBox.querySelector('.chat-time.incoming-time:last-child');
      if (lastIncomingTimestamp) {
        Elements.chatBox.insertBefore(faqMessageLi, lastIncomingTimestamp);
      } else {
        Elements.chatBox.appendChild(faqMessageLi);
      }

      // Save current options state
      State.currentOptions = filteredOptions.map(option => ({
        text: option,
        type: "standard",
      }));

      this.checkForActiveOptions();
      State.save();
    },


    showChatMessageOptions(chatMessageOptions) {
      if (!chatMessageOptions || chatMessageOptions.length === 0) return;

      // Create chat message with options
      const optionsLi = document.createElement("li");
      optionsLi.className = "chat incoming";

      // Create options container
      const chatMessageOptionsContainer = document.createElement("div");
      chatMessageOptionsContainer.className = "chat-message-options";

      const optionsContainer = document.createElement("div");
      optionsContainer.className = "chat-options-container";

      // Add each option
      chatMessageOptions.forEach((option) => {
        if (!State.userSelectedOptions.includes(option.toLowerCase())) {
          const optionDiv = document.createElement("div");
          optionDiv.className = "chat-option";
          optionDiv.setAttribute("data-option", option);
          optionDiv.setAttribute("data-option-type", "chat-message");
          optionDiv.textContent = option;

          const optionIcon = document.createElement("img");
          optionIcon.src = "/static/assets/icons/arrow-right.svg";
          optionIcon.alt = "Option Icon";
          optionIcon.className = "option-icon";
          optionIcon.style.filter = "invert(22%) sepia(94%) saturate(7450%) hue-rotate(237deg) brightness(100%) contrast(103%)";

          optionDiv.appendChild(optionIcon);
          optionDiv.addEventListener("click", () => this.handleOptionClick(option));
          optionsContainer.appendChild(optionDiv);
        }
      });

      // Only add options if there are any unselected options
      if (optionsContainer.children.length > 0) {
        chatMessageOptionsContainer.appendChild(optionsContainer);
        optionsLi.appendChild(chatMessageOptionsContainer);
        Elements.chatBox.appendChild(optionsLi);
        Elements.chatBox.appendChild(UIComponents.createTimeStamp("incoming"));

        // Store current options for later reattachment
        State.currentOptions = chatMessageOptions.map((option) => ({
          text: option,
          type: "chat-message"
        }));

        // Update input state and save
        this.checkForActiveOptions();
        Elements.chatBox.scrollTo({ top: Elements.chatBox.scrollHeight, behavior: 'smooth' });
        State.save();
        sessionStorage.setItem("jobContainerIsLast", "false");
      }
    },

    reattachChatMessageOptions() {
      const chatMessageOptions = document.querySelectorAll(".chat-message-options .chat-option");

      chatMessageOptions.forEach(option => {
        const newOption = option.cloneNode(true);
        option.parentNode.replaceChild(newOption, option);

        const optionText = newOption.getAttribute("data-option");
        if (optionText && !State.userSelectedOptions.includes(optionText.toLowerCase())) {
          newOption.addEventListener("click", () => this.handleOptionClick(optionText));

          // Ensure icon is present
          let optionIcon = newOption.querySelector('.option-icon');
          if (!optionIcon) {
            optionIcon = document.createElement("img");
            optionIcon.src = "/static/assets/icons/arrow-right.svg";
            optionIcon.alt = "Option Icon";
            optionIcon.className = "option-icon";
            optionIcon.style.filter = "invert(15%) sepia(95%) saturate(7458%) hue-rotate(340deg) brightness(101%) contrast(96%)";
            newOption.appendChild(optionIcon);
          }
        }
      });

      this.checkForActiveOptions();
    },

    reattachChatMessageOptions() {
      const chatMessageOptions = document.querySelectorAll(".chat-message-options .chat-option");

      chatMessageOptions.forEach(option => {
        // Remove existing listeners by cloning
        const newOption = option.cloneNode(true);
        option.parentNode.replaceChild(newOption, option);

        // Get the option text from the data attribute
        const optionText = newOption.getAttribute("data-option");

        if (optionText) {
          // Reattach click handler
          newOption.addEventListener("click", () => this.handleOptionClick(optionText));

          // Ensure icon is present
          let optionIcon = newOption.querySelector('.option-icon');
          if (!optionIcon) {
            optionIcon = document.createElement("img");
            optionIcon.src = "/static/assets/icons/arrow-right.svg";
            optionIcon.alt = "Option Icon";
            optionIcon.className = "option-icon";
            optionIcon.style.filter = "invert(15%) sepia(95%) saturate(7458%) hue-rotate(340deg) brightness(101%) contrast(96%)";
            newOption.appendChild(optionIcon);
          }
        }
      });

      // Update input state
      this.checkForActiveOptions();
    },
  };

  // Event Handlers
  const EventHandlers = {
    setupInputHandlers() {
      Elements.chatInput.addEventListener("input", () => {
        // Reset height to measure scroll height accurately
        Elements.chatInput.style.height = "20px";

        // Calculate new height while respecting max height
        const newHeight = Math.min(
          Elements.chatInput.scrollHeight,
          CONSTANTS.MAX_INPUT_HEIGHT
        );

        // Set new height
        Elements.chatInput.style.height = `${newHeight}px`;

        // Enable scrolling if content exceeds max height
        Elements.chatInput.style.overflowY =
          Elements.chatInput.scrollHeight > CONSTANTS.MAX_INPUT_HEIGHT
            ? "auto"
            : "hidden";

        // Limit input length
        if (Elements.chatInput.value.length > CONSTANTS.MAX_INPUT_LENGTH) {
          Elements.chatInput.value = Elements.chatInput.value.slice(
            0,
            CONSTANTS.MAX_INPUT_LENGTH
          );
        }
      });

      Elements.chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          if (Elements.chatInput.value.trim()) {
            ChatHandler.handleChat();
            // Reset input height after sending
            Elements.chatInput.style.height = "20px";
            Elements.chatInput.style.overflowY = "hidden";
          }
        }
      });
    },

    setupChatbotToggle() {
      Elements.chatToggle.addEventListener("click", () => {
        const chatBot = document.querySelector("#chatBot");
        const avatar = document.querySelector(".chatbot header .avatar");

        chatBot.classList.toggle("show-chatbot");
        const isVisible = chatBot.classList.contains("show-chatbot");

        if (isVisible) {
          Elements.chatPopup.classList.remove("show");
          parent.postMessage({ action: "expand" }, "*");
          //avatar.classList.add('animate');

          if (State.firstClick) {
            State.firstClick = false;
            setTimeout(async () => {
              Elements.chatBox.appendChild(
                UIComponents.createTimeStamp("center")
              );
              await ChatHandler.fetchBotResponses("hi");
              await ChatHandler.handleBotReply("hi");
              State.save();
              Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);
            }, CONSTANTS.TYPING_DELAY);
          }
        } else {
          parent.postMessage({ action: "collapse" }, "*");
          //avatar.classList.remove('animate');
        }
      });

      Elements.chatPopup.addEventListener("click", () => {
        const chatBotContainer = document.querySelector("#chatBot");
        const avatar = document.querySelector(".chatbot header .avatar");

        chatBotContainer.classList.toggle("show-chatbot");
        const isVisible = chatBotContainer.classList.contains("show-chatbot");

        if (isVisible) {
          parent.postMessage({ action: "expand" }, "*");
          avatar.classList.add("animate");

          if (State.firstClick) {
            State.firstClick = false;
            setTimeout(async () => {
              Elements.chatBox.appendChild(
                UIComponents.createTimeStamp("center")
              );
              await ChatHandler.fetchBotResponses("hi");
              await ChatHandler.handleBotReply("hi");
              State.save();
              Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);
            }, CONSTANTS.TYPING_DELAY);
          }
        } else {
          parent.postMessage({ action: "collapse" }, "*");
          avatar.classList.remove("animate");
        }
      });
    },

    setupBroomHandler() {
      const broomIcon = document.querySelector(".broom-icon");
      broomIcon.addEventListener("click", async () => {
        State.clear();
        Elements.chatBox.innerHTML = "";
        Elements.optionsContainer.innerHTML = "";
        // Generate new sectionId for new session
        State.sectionId = CookieManager.generateSectionId();
        State.save();
        // Show initial greeting
        setTimeout(async () => {
          Elements.chatBox.appendChild(UIComponents.createTimeStamp("center"));
          await ChatHandler.fetchBotResponses("hi");
          await ChatHandler.handleBotReply("hi");
        }, CONSTANTS.TYPING_DELAY);
      });
    },

    setupOptionsScroll() {
      let scrollAmount = 0;
      let scrollDirection = 1;
      let isDragging = false;
      let startX, scrollStartLeft;
      let scrollInterval;
      let lastTimestamp = 0;
      let lastScrollPosition = 0;

      function autoScroll(timestamp) {
        if (!lastTimestamp) lastTimestamp = timestamp;
        if (isDragging) return;

        const deltaTime = Math.min(
          timestamp - lastTimestamp,
          CONSTANTS.MAX_DELTA_TIME
        );
        lastTimestamp = timestamp;

        const maxScrollLeft =
          Elements.optionsContainer.scrollWidth -
          Elements.optionsContainer.clientWidth;
        scrollAmount +=
          scrollDirection * deltaTime * CONSTANTS.SCROLL_SPEED_MULTIPLIER;

        if (scrollAmount >= maxScrollLeft || scrollAmount <= 0) {
          scrollDirection *= -1;
          scrollAmount = Math.max(0, Math.min(scrollAmount, maxScrollLeft));
        }

        Elements.optionsContainer.scrollLeft = scrollAmount;
        scrollInterval = requestAnimationFrame(autoScroll);
      }

      Elements.optionsContainer.addEventListener("mouseover", () => {
        cancelAnimationFrame(scrollInterval);
        lastScrollPosition = Elements.optionsContainer.scrollLeft;
      });

      Elements.optionsContainer.addEventListener("mouseleave", () => {
        if (!isDragging) {
          scrollAmount = lastScrollPosition;
          scrollInterval = requestAnimationFrame(autoScroll);
        }
      });

      Elements.optionsContainer.addEventListener("mousedown", (e) => {
        isDragging = true;
        startX = e.pageX - Elements.optionsContainer.offsetLeft;
        scrollStartLeft = Elements.optionsContainer.scrollLeft;
        Elements.optionsContainer.classList.add("dragging");
        cancelAnimationFrame(scrollInterval);
      });

      document.addEventListener("mouseup", () => {
        if (isDragging) {
          isDragging = false;
          Elements.optionsContainer.classList.remove("dragging");
          lastScrollPosition = Elements.optionsContainer.scrollLeft;
          scrollAmount = lastScrollPosition;
        }
      });

      Elements.optionsContainer.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        e.preventDefault();
        const x = e.pageX - Elements.optionsContainer.offsetLeft;
        const walk = (x - startX) * 1;
        Elements.optionsContainer.scrollLeft = scrollStartLeft - walk;
      });

      // Similar updates for touch events
      Elements.optionsContainer.addEventListener("touchstart", (e) => {
        isDragging = true;
        startX = e.touches[0].pageX - Elements.optionsContainer.offsetLeft;
        scrollStartLeft = Elements.optionsContainer.scrollLeft;
        Elements.optionsContainer.classList.add("dragging");
        cancelAnimationFrame(scrollInterval);
      });

      Elements.optionsContainer.addEventListener("touchend", () => {
        if (isDragging) {
          isDragging = false;
          Elements.optionsContainer.classList.remove("dragging");
          lastScrollPosition = Elements.optionsContainer.scrollLeft;
          scrollAmount = lastScrollPosition;
        }
      });

      Elements.optionsContainer.addEventListener("touchmove", (e) => {
        if (!isDragging) return;
        e.preventDefault();
        const x = e.touches[0].pageX - Elements.optionsContainer.offsetLeft;
        const walk = (x - startX) * 1;
        Elements.optionsContainer.scrollLeft = scrollStartLeft - walk;
      });

      scrollInterval = requestAnimationFrame(autoScroll);

      window.addEventListener("beforeunload", () => {
        cancelAnimationFrame(scrollInterval);
      });
    },
    setupMenu() {
      const headerBody = document.querySelector(".chat-opt-menu");
      const menu = UIComponents.createMenu();
      headerBody.appendChild(menu);

      const menuButton = menu.querySelector(".menu-toggle");
      const menuOverlay = menu.querySelector(".menu-overlay");
      const menuDropdown = menu.querySelector(".menu-dropdown");
      const chatbot = document.querySelector(".chatbot");
      const regularChatInput = document.querySelector(".chat-input");

      if (!menuButton || !menuOverlay || !menuDropdown || !regularChatInput) {
        console.error("Menu or input elements not found!");
        return;
      }

      const combinedMenuContainer = document.createElement("div");
      combinedMenuContainer.className = "combined-menu-container";

      const menuBottomRow = document.createElement("div");
      menuBottomRow.className = "menu-bottom-row";

      const closeButton = document.createElement("div");
      closeButton.className = "menu-close-btn";
      closeButton.innerHTML = `<img src="/static/assets/icons/menuclose.svg" alt="Close Menu">`;

      const menuChatInput = regularChatInput.cloneNode(true);
      menuChatInput.className = "menu-chat-input";

      menuBottomRow.appendChild(closeButton);
      menuBottomRow.appendChild(menuChatInput);

      if (menuDropdown.parentNode) {
        menuDropdown.parentNode.removeChild(menuDropdown);
      }

      combinedMenuContainer.appendChild(menuDropdown);
      combinedMenuContainer.appendChild(menuBottomRow);
      document.querySelector(".chat-with-menu").appendChild(combinedMenuContainer);

      combinedMenuContainer.style.display = "none";

      menuButton.addEventListener("click", (e) => {
        e.stopPropagation();
        chatbot.classList.add("menu-open");
        combinedMenuContainer.style.display = "flex";
        regularChatInput.style.display = "none";
        menuButton.querySelector("img").src = "/static/assets/icons/menuclose.svg";
        menuDropdown.style.display = "flex";
      });

      function closeMenu() {
        chatbot.classList.remove("menu-open");
        combinedMenuContainer.style.display = "none";
        regularChatInput.style.display = "flex";
        menuButton.querySelector("img").src = "/static/assets/icons/menu.svg";
      }

      document.addEventListener("click", (e) => {
        if (chatbot.classList.contains("menu-open")) {
          if (!combinedMenuContainer.contains(e.target) && !menuButton.contains(e.target)) {
            closeMenu();
          }
        }
      });

      closeButton.addEventListener("click", closeMenu);

      const menuTextarea = menuChatInput.querySelector("textarea");
      const menuSendBtn = menuChatInput.querySelector("img");

      if (!menuTextarea || !menuSendBtn) {
        console.error("Menu input or send button not found.");
        return;
      }

      menuTextarea.style.color = "black";
      menuTextarea.style.placeholder = "rgba(0, 0, 0, 0.4)";

      menuSendBtn.addEventListener("click", () => {
        const message = menuTextarea.value.trim();
        if (message) {
          const regularTextarea = regularChatInput.querySelector("textarea");
          regularTextarea.value = message;
          closeMenu();
          menuTextarea.value = "";
          setTimeout(() => {
            const regularSendBtn = regularChatInput.querySelector("img");
            regularSendBtn.click();
          }, 10);
        }
      });

      menuTextarea.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          menuSendBtn.click();
        }
      });

      menuDropdown.addEventListener("click", async (e) => {
        const action = e.target.dataset.action;
        if (!action) return;

        closeMenu();

        switch (action) {
          case "start-project":
            await ChatHandler.handleOptionClick("Start a project");
            break;
          case "career":
            await ChatHandler.handleOptionClick("Looking for a job");
            break;
          case "explore":
            await ChatHandler.handleOptionClick("Explore services");
            break;
          case "clear":
            State.clear();
            Elements.chatBox.innerHTML = "";
            Elements.optionsContainer.innerHTML = "";
            State.sectionId = CookieManager.generateSectionId();
            State.save();
            setTimeout(async () => {
              Elements.chatBox.appendChild(UIComponents.createTimeStamp("center"));
              await ChatHandler.fetchBotResponses("hi");
              await ChatHandler.handleBotReply("hi");
            }, CONSTANTS.TYPING_DELAY);
            break;
        }
      });
    },

    // Setup close button handler
    setupCloseButton() {
      Elements.closeButton.addEventListener("click", () => {
        parent.postMessage({ action: "collapse" }, "*");
        document.querySelector("#chatBot").classList.remove("show-chatbot");
        document
          .querySelector(".chatbot header .avatar")
          .classList.remove("animate");
      });
    },

    // Setup send button handler
    setupSendButton() {
      document.querySelector('#send-btn').addEventListener("click", () => { ChatHandler.handleChat() }
      );
    },

    // Initialize all event handlers
    init() {
      this.setupInputHandlers();
      this.setupChatbotToggle();
      // this.setupOptionsScroll();
      this.setupCloseButton();
      this.setupMenu();
      this.setupSendButton();
      this.setupBroomHandler();
    },
  };

  // Main initialization function
  const initialize = () => {
    // Initialize DOM elements
    Elements.init();

    // Initialize Tab Visibility Handler
    TabVisibilityHandler.init();

    // Try to load existing state
    const stateLoaded = State.load();

    if (stateLoaded) {
      // console.log("Previous session restored");
      TabVisibilityHandler.checkStateValidity();
    } else {
      // Check if a session ID already exists in sessionStorage
      const existingSectionId = sessionStorage.getItem("chatbotSectionId");
      if (existingSectionId) {
        State.sectionId = existingSectionId;
      } else {
        // Generate new sectionId only if no existing session ID
        State.sectionId = CookieManager.generateSectionId();
        sessionStorage.setItem("chatbotSectionId", State.sectionId);
      }
      State.save();
    }

    // Setup event handlers
    EventHandlers.init();

    // Restore scroll position if needed
    if (stateLoaded) {
      Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);
    }

    // console.log(`Chatbot initialization complete (${stateLoaded ? "restored" : "new"} session)`);
  };

  // Public API remains the same
  return {
    init: initialize,
    reloadChat: () => {
      State.load();
      setTimeout(() => {
        Elements.chatBox.scrollTo(0, Elements.chatBox.scrollHeight);
        UIComponents.reattachMessageHandlers?.();
        ChatHandler.checkForActiveOptions();
      }, 200);
    },
    clearChat: () => {
      State.clear();
      // console.log("Chat history and section ID cleared");
    },
  };
})();
// Initialize the chatbot when the DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  ChatbotModule.init();
});

// toast messasge
window.onload = function () {
  const toast = document.getElementById("toast");
  const closeBtn = document.getElementById("toast-close-btn");
  const chatBot = document.querySelector("#chatBot");
  const chatbotCloseButton = document.getElementById("chatbot-close-btn");
  const arrowChat = document.querySelector(".toast-arrow-down");

  let isChatbotOpen = false;
  let hasToastShown = false;

  if (arrowChat) {
    arrowChat.style.display = "none";
    arrowChat.style.opacity = "0";
    arrowChat.style.transition = "opacity 0.3s ease-in-out";
  }

  const updateArrowVisibility = (show) => {
    if (arrowChat) {
      if (show) {
        arrowChat.style.display = "block";
        requestAnimationFrame(() => {
          arrowChat.style.opacity = "1";
        });
      } else {
        arrowChat.style.opacity = "0";
        setTimeout(() => {
          arrowChat.style.display = "none";
        }, 300);
      }
    }
  };

  const showToastWithTypingAnimation = () => {
    const toastMessage = '"I’m your digital assistant, here to decode your doubts."';

    if (!toast || !closeBtn) return;

    toast.innerHTML = "";
    toast.style.display = "block";
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease-in-out";

    requestAnimationFrame(() => {
      updateArrowVisibility(true);
      toast.style.opacity = "1";

      setTimeout(() => {
        let index = 0;
        const typingInterval = setInterval(function () {
          toast.innerHTML += toastMessage[index];
          index++;

          if (index === toastMessage.length) {
            clearInterval(typingInterval);
            closeBtn.classList.add("show");
          }
        }, 50);
      }, 300);
    });
  };

  setTimeout(function () {
    if (!isChatbotOpen && !hasToastShown) {
      parent.postMessage({ action: "expandToast" }, "*");
      showToastWithTypingAnimation();
      hasToastShown = true;
    }
  }, 2000);

  closeBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    toast.style.opacity = "0";
    updateArrowVisibility(false);

    setTimeout(() => {
      toast.style.display = "none";
      closeBtn.classList.remove("show");
    }, 300);

    parent.postMessage({ action: "collapseToast" }, "*");
  });

  toast.addEventListener("click", function () {
    toast.classList.remove("show");
    chatBot.classList.add("show-chatbot");
    toast.style.opacity = "0";
    updateArrowVisibility(false);

    setTimeout(() => {
      toast.style.display = "none";
      closeBtn.classList.remove("show");
    }, 300);

    parent.postMessage({ action: "expand" }, "*");
  });

  const chatbotToggle = document.querySelector(".chatbot-toggle");

  chatbotToggle.addEventListener("click", function () {
    isChatbotOpen = !isChatbotOpen;
    const isMobile = window.innerWidth <= 768;

    if (isChatbotOpen) {
      toast.classList.remove("show");
      toast.style.opacity = "0";
      updateArrowVisibility(false);

      if (isMobile) {
        setTimeout(() => {
          toast.style.display = "none";
          closeBtn.classList.remove("show");
          updateArrowVisibility(false);
        }, 300);
      }
    } else {
      updateArrowVisibility(false);
    }
  });

  chatbotCloseButton.addEventListener("click", function () {
    chatBot.classList.remove("show-chatbot");
    isChatbotOpen = false;
    updateArrowVisibility(false);
    parent.postMessage({ action: "collapse" }, "*");

    if (hasToastShown) {
      toast.classList.remove("show");
      toast.style.opacity = "0";

      setTimeout(() => {
        toast.style.display = "none";
        closeBtn.classList.remove("show");
      }, 300);
    }
  });

  window.addEventListener("resize", () => {
    const isMobile = window.innerWidth <= 768;

    if (isMobile && isChatbotOpen) {
      toast.classList.remove("show");
      toast.style.opacity = "0";
      updateArrowVisibility(false);

      setTimeout(() => {
        toast.style.display = "none";
        closeBtn.classList.remove("show");
      }, 300);
    }
  });
};