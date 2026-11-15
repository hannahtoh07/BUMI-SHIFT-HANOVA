
/*
 BUMI SHIFT 6.3 — Ask BUMI
 Genuine Gemini chat
 Saved conversation + automatic retries
*/

(() => {
  "use strict";

  const $ = id => document.getElementById(id);

  const chat = $("bumiChat");
  const input = $("bumiQuestion");
  const sendButton = $("bumiSend");
  const clearButton = $("bumiClear");
  const status = $("bumiStatus");

  if (!chat || !input || !sendButton ||
      !clearButton || !status) return;

  const style = document.createElement("style");

  style.textContent = `
    #bumiChat {
      display:flex;
      flex-direction:column;
      gap:12px;
      max-height:480px;
      min-height:150px;
      overflow-y:auto;
      padding:16px;
      margin:14px 0;
      background:#f4f7fc;
      border:1px solid #dce5ef;
      border-radius:14px;
    }

    .bumiBubble {
      max-width:90%;
      padding:12px 15px;
      border-radius:13px;
      line-height:1.65;
      white-space:pre-wrap;
      overflow-wrap:anywhere;
      color:#102b50;
    }

    .bumiBubble.user {
      align-self:flex-end;
      background:#dcecff;
    }

    .bumiBubble.assistant {
      align-self:flex-start;
      background:#fff;
      border:1px solid #dce5ef;
    }

    .bumiBubble.pending {
      align-self:flex-start;
      background:#e9effa;
      color:#526a87;
    }

    .bumiCompose {
      display:flex;
      gap:10px;
      align-items:flex-end;
    }

    .bumiCompose textarea {
      flex:1;
      min-height:75px;
      min-width:0;
    }

    .bumiFooter {
      display:flex;
      justify-content:space-between;
      align-items:center;
      flex-wrap:wrap;
      gap:12px;
      margin-top:10px;
      color:#526a87;
      font-size:12px;
    }

    #bumiClear {
      background:#e7effa;
      color:#102b50;
      padding:8px 12px;
      font-size:12px;
    }

    .bumiRetry {
      margin-top:10px;
      background:#2069d4;
      color:white;
      display:block;
    }

    @media(max-width:600px) {
      .bumiCompose {
        flex-direction:column;
        align-items:stretch;
      }

      .bumiBubble {
        max-width:97%;
      }
    }
  `;

  document.head.append(style);

  const STORAGE_KEY = "bumi_shift_chat_v63";
  const MAX_MESSAGES = 24;

  let messages = [];
  let pending = null;
  let busy = false;
  let generation = 0;
  let activeController = null;

  function save() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          messages: messages.slice(-MAX_MESSAGES),
          pending
        })
      );
    } catch (_) {
      // Conversation still works in this browser tab.
    }
  }

  function restore() {
    try {
      const saved = JSON.parse(
        localStorage.getItem(STORAGE_KEY) || "{}"
      );

      if (Array.isArray(saved.messages)) {
        messages = saved.messages.filter(m =>
          m &&
          ["user","assistant"].includes(m.role) &&
          typeof m.content === "string"
        ).slice(-MAX_MESSAGES);
      }

      if (
        saved.pending &&
        typeof saved.pending.question === "string" &&
        saved.pending.farm
      ) {
        pending = saved.pending;
      }
    } catch (_) {
      messages = [];
      pending = null;
    }
  }

  function bubble(role, content) {
    const element = document.createElement("div");

    element.className = "bumiBubble " + role;
    element.textContent = content;

    chat.appendChild(element);
    chat.scrollTop = chat.scrollHeight;

    return element;
  }

  function retryCard() {
    const box = bubble(
      "assistant",
      "Your question is saved. Continue when you're ready."
    );

    const button = document.createElement("button");
    button.className = "bumiRetry";
    button.textContent = "Continue";

    button.onclick = () => {
      if (!busy) submit(true);
    };

    box.appendChild(button);
  }

  function render() {
    chat.replaceChildren();

    if (!messages.length && !pending) {
      bubble(
        "assistant",
        "What would you like to explore about your farm?"
      );
    }

    messages.forEach(message => {
      bubble(message.role, message.content);
    });

    if (pending) {
      bubble("user", pending.question);
      if (!busy) retryCard();
    }
  }

  function farmContext() {
    const context = window.BUMIContext || {};

    return {
      latitude: Number(context.latitude ?? 1.46),
      longitude: Number(context.longitude ?? 110.49),
      priority: $("priority")?.value || "soil",
      baseline: $("baseline")?.value || "rice",
      selected_crop: context.selected_crop || null,
      selected_rotation: context.selected_rotation || null
    };
  }

  function setBusy(value) {
    busy = value;
    sendButton.disabled = value;
    input.disabled = value;
    sendButton.textContent = value
      ? "Thinking..."
      : "Send";
  }

  async function requestAnswer(question, farm, history) {
    const controller = new AbortController();
    activeController = controller;

    const timeout = setTimeout(
      () => controller.abort(),
      105000
    );

    try {
      const response = await fetch("/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        signal: controller.signal,
        body: JSON.stringify({
          question,
          ...farm,
          history
        })
      });

      const data = await response.json().catch(() => ({}));

      if (
        !response.ok ||
        data.generated_by !== "Gemini" ||
        typeof data.answer !== "string" ||
        !data.answer.trim()
      ) {
        const error = new Error("Request not completed");

        error.retryable =
          data.detail?.retryable !== false;

        throw error;
      }

      return data.answer.trim();

    } finally {
      clearTimeout(timeout);

      if (activeController === controller) {
        activeController = null;
      }
    }
  }

  async function submit(resume = false) {
    if (busy) return;

    if (!resume) {
      const question = input.value.trim();
      if (!question) return;

      pending = {
        question,
        farm: farmContext()
      };

      input.value = "";
      save();
    }

    if (!pending) return;

    const current = pending;
    const currentGeneration = generation;

    setBusy(true);
    render();

    status.textContent =
      "BUMI is reviewing your farming question...";

    const loading = bubble(
      "pending",
      "Looking at the evidence and possible farming options..."
    );

    try {
      const answer = await requestAnswer(
        current.question,
        current.farm,
        messages.slice(-12)
      );

      if (currentGeneration !== generation) return;

      messages.push(
        {
          role: "user",
          content: current.question
        },
        {
          role: "assistant",
          content: answer
        }
      );

      messages = messages.slice(-MAX_MESSAGES);
      pending = null;

      save();

      status.textContent = "Powered by Gemini";

    } catch (_) {
      if (currentGeneration !== generation) return;

      status.textContent = "Question saved";

    } finally {
      loading.remove();

      if (currentGeneration === generation) {
        setBusy(false);
        render();
      }
    }
  }

  sendButton.addEventListener("click", () => {
    submit(false);
  });

  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit(false);
    }
  });

  clearButton.addEventListener("click", () => {
    generation++;

    if (activeController) {
      activeController.abort();
      activeController = null;
    }

    messages = [];
    pending = null;

    setBusy(false);
    save();
    render();

    status.textContent = "Powered by Gemini";
  });

  restore();
  render();
})();
