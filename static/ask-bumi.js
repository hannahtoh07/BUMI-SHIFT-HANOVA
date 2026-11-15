
/*
 BUMI SHIFT 6.3
 Genuine Gemini chat with saved conversation
 and automatic backend retry.
*/

(() => {
  const old = document.getElementById("ask");

  if (!old) return;

  const style = document.createElement("style");

  style.textContent = `
    #ask .bumi-thread {
      display:flex;
      flex-direction:column;
      gap:12px;
      max-height:470px;
      overflow:auto;
      padding:15px;
      margin:14px 0;
      background:#f3f7fc;
      border:1px solid #dbe5ef;
      border-radius:14px;
    }

    #ask .bumi-bubble {
      max-width:90%;
      padding:12px 15px;
      border-radius:14px;
      color:#102b50;
      white-space:pre-wrap;
      overflow-wrap:anywhere;
      line-height:1.65;
    }

    #ask .bumi-user {
      align-self:flex-end;
      background:#dcecff;
    }

    #ask .bumi-ai {
      align-self:flex-start;
      background:white;
      border:1px solid #dbe5ef;
    }

    #ask .bumi-compose {
      display:flex;
      gap:9px;
      align-items:end;
    }

    #ask .bumi-compose textarea {
      flex:1;
      min-width:0;
      min-height:76px;
    }

    #ask .bumi-footer {
      display:flex;
      justify-content:space-between;
      gap:10px;
      align-items:center;
      margin-top:10px;
      flex-wrap:wrap;
    }

    #ask .bumi-secondary {
      background:#e8f0fc;
      color:#102b50;
    }

    #ask .bumi-small {
      color:#526985;
      font-size:12px;
    }

    @media(max-width:600px) {
      #ask .bumi-compose {
        flex-direction:column;
        align-items:stretch;
      }

      #ask .bumi-bubble {
        max-width:98%;
      }
    }
  `;

  document.head.append(style);

  old.replaceChildren();

  old.innerHTML = `
    <div class="eyebrow">
      Your farming companion
    </div>

    <h2>Ask BUMI</h2>

    <p class="muted">
      Ask about crop rotations, soil health,
      growing conditions or ways to shift
      your farming practices.
    </p>

    <div
      id="bumiThread"
      class="bumi-thread"
      role="log"
      aria-live="polite">
    </div>

    <div class="bumi-compose">
      <textarea
        id="bumiInput"
        aria-label="Ask BUMI"
        placeholder="How could I improve soil health while continuing to grow rice?">
      </textarea>

      <button
        type="button"
        id="bumiSend">
        Send
      </button>
    </div>

    <div class="bumi-footer">
      <span
        id="bumiState"
        class="bumi-small">
        Powered by Gemini
      </span>

      <button
        type="button"
        class="bumi-secondary"
        id="bumiClear">
        New conversation
      </button>
    </div>
  `;

  const $ = id => document.getElementById(id);

  const key = "bumi-chat-v63";

  let messages = [];
  let pending = null;
  let busy = false;
  let epoch = 0;

  // Restore saved chat.
  try {
    const saved = JSON.parse(
      localStorage.getItem(key) || "{}"
    );

    if (Array.isArray(saved.messages)) {
      messages = saved.messages.filter(
        m =>
          ["user", "assistant"].includes(m.role)
          && typeof m.content === "string"
      ).slice(-20);
    }

    if (
      saved.pending
      && typeof saved.pending.question === "string"
    ) {
      pending = saved.pending;
    }

  } catch (_) {
    messages = [];
  }

  function save() {
    try {
      localStorage.setItem(
        key,
        JSON.stringify({
          messages: messages.slice(-20),
          pending
        })
      );
    } catch (_) {
      // Browser storage may be disabled.
    }
  }

  function bubble(role, content) {
    const node = document.createElement("div");

    node.className =
      "bumi-bubble "
      + (role === "user"
        ? "bumi-user"
        : "bumi-ai");

    node.textContent = content;

    $("bumiThread").append(node);

    $("bumiThread").scrollTop =
      $("bumiThread").scrollHeight;

    return node;
  }

  function render() {
    $("bumiThread").replaceChildren();

    if (!messages.length && !pending) {
      bubble(
        "assistant",
        "What would you like to explore about your farm?"
      );
    }

    messages.forEach(m => {
      bubble(m.role, m.content);
    });

    if (pending) {
      bubble("user", pending.question);
      retryCard();
    }
  }

  function retryCard() {
    const node = bubble(
      "assistant",
      "Your question is saved. Tap Continue to finish the answer."
    );

    const btn = document.createElement("button");

    btn.textContent = "Continue";
    btn.style.marginTop = "10px";

    btn.onclick = () => {
      node.remove();
      send(true);
    };

    node.append(btn);
  }

  function context() {
    const c = window.BUMIContext || {};

    return {
      latitude: Number(
        c.latitude ?? 1.46
      ),
      longitude: Number(
        c.longitude ?? 110.49
      ),
      priority:
        $("priority")?.value || "soil",
      baseline:
        $("baseline")?.value || "rice",
      selected_crop:
        c.selected_crop || null,
      selected_rotation:
        c.selected_rotation || null
    };
  }

  async function askOnce(
    question,
    farm,
    history
  ) {
    const controller = new AbortController();

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

      const data = await response.json()
        .catch(() => ({}));

      if (
        !response.ok
        || data.generated_by !== "Gemini"
        || !data.answer?.trim()
      ) {
        const error = new Error(
          "No completed answer"
        );

        error.retryable =
          data.detail?.retryable !== false;

        throw error;
      }

      return data.answer.trim();

    } finally {
      clearTimeout(timeout);
    }
  }

  async function send(resume = false) {
    if (busy) return;

    if (!resume) {
      const question =
        $("bumiInput").value.trim();

      if (!question) return;

      pending = {
        question,
        farm: context()
      };

      $("bumiInput").value = "";

      save();
      render();
    }

    if (!pending) return;

    const myEpoch = epoch;

    busy = true;
    $("bumiSend").disabled = true;

    $("bumiState").textContent =
      "BUMI is reviewing your question…";

    render();

    const loading = bubble(
      "assistant",
      "Looking at the evidence and possible farming options…"
    );

    try {
      const answer = await askOnce(
        pending.question,
        pending.farm,
        messages.slice(-12)
      );

      if (myEpoch !== epoch) return;

      messages.push(
        {
          role: "user",
          content: pending.question
        },
        {
          role: "assistant",
          content: answer
        }
      );

      messages = messages.slice(-20);

      pending = null;

      save();
      render();

      $("bumiState").textContent =
        "Powered by Gemini";

    } catch (_) {
      if (myEpoch !== epoch) return;

      loading.remove();
      render();

      $("bumiState").textContent =
        "Question saved";

    } finally {
      busy = false;
      $("bumiSend").disabled = false;
    }
  }

  $("bumiSend").onclick = () => {
    send(false);
  };

  $("bumiInput").onkeydown = event => {
    if (
      event.key === "Enter"
      && !event.shiftKey
    ) {
      event.preventDefault();
      send(false);
    }
  };

  $("bumiClear").onclick = () => {
    epoch++;

    messages = [];
    pending = null;

    save();
    render();

    $("bumiState").textContent =
      "Powered by Gemini";
  };

  render();
})();
