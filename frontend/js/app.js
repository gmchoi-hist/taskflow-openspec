(() => {
  let currentUser = null;
  let team = null;
  let members = [];
  let currentFilter = 'all';
  let currentView = 'kanban';
  let lastMessageSince = null;
  let pollTimer = null;
  let pendingDeleteHandler = null;

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function showForbidden() {
    $('#app-view').classList.add('hidden');
    $('#forbidden-view').classList.remove('hidden');
  }

  function switchView(view) {
    currentView = view;
    ['kanban', 'chat', 'members'].forEach((v) => {
      $(`#view-${v}`).classList.toggle('hidden', v !== view);
    });
    $$('.nav-btn').forEach((btn) => {
      btn.classList.toggle('bg-[#0a84ff]', btn.dataset.view === view);
      btn.classList.toggle('text-white', btn.dataset.view === view);
    });
    $('#mobile-drawer').classList.add('hidden');

    if (view === 'kanban') loadTasks();
    if (view === 'chat') startChatPolling();
    else stopChatPolling();
    if (view === 'members') loadMembers();
  }

  function stopChatPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function startChatPolling() {
    stopChatPolling();
    lastMessageSince = null;
    $('#chat-messages').innerHTML = '';
    loadMessages();
    // 5초 고정 폴링 (모바일에서도 동일 — 동적 단축/backoff 없음)
    pollTimer = setInterval(loadMessages, 5000);
  }

  // ---------- 초기화 ----------
  async function init() {
    if (!requireAuthOrRedirect()) return;

    try {
      currentUser = await apiFetch('/auth/me');
    } catch (e) {
      return; // 401은 api.js가 이미 /login.html로 리다이렉트
    }

    if (!currentUser.team_id) {
      location.href = '/team-select.html';
      return;
    }

    try {
      team = await apiFetch(`/teams/${currentUser.team_id}`);
    } catch (e) {
      if (e.code === 'FORBIDDEN') {
        showForbidden();
        return;
      }
      throw e;
    }

    $('#app-view').classList.remove('hidden');
    $('#user-email').textContent = currentUser.email;
    $('#mobile-user-email').textContent = currentUser.email;
    $('#mobile-avatar').textContent = currentUser.email[0].toUpperCase();
    $('#team-name').textContent = `${team.name} 팀`;
    $('#mobile-team-role').textContent = `${team.name} · ${team.owner_id === currentUser.id ? 'owner' : 'member'}`;

    await loadMembers();
    switchView('kanban');
  }

  $('#forbidden-back-btn').addEventListener('click', () => location.reload());

  $('#hamburger-btn').addEventListener('click', () => {
    $('#mobile-drawer').classList.toggle('hidden');
  });

  $$('.nav-btn, .nav-btn-mobile').forEach((btn) => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  async function doLogout() {
    try { await apiFetch('/auth/logout', { method: 'POST' }); } catch (e) {}
    clearToken();
    location.href = '/login.html';
  }
  $('#logout-btn').addEventListener('click', doLogout);
  $('#logout-btn-mobile').addEventListener('click', doLogout);

  // ---------- 칸반 ----------
  $$('.filter-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      currentFilter = btn.dataset.filter;
      $$('.filter-btn').forEach((b) => b.classList.toggle('bg-[#0a84ff]', b === btn));
      $$('.filter-btn').forEach((b) => b.classList.toggle('text-white', b === btn));
      loadTasks();
    });
  });
  $('[data-filter="all"]').classList.add('bg-[#0a84ff]', 'text-white');

  async function loadTasks() {
    const qs = currentFilter === 'all' ? '' : `?filter=${currentFilter}`;
    let tasks;
    try {
      tasks = await apiFetch(`/teams/${team.id}/tasks${qs}`);
    } catch (e) {
      if (e.code === 'FORBIDDEN') return showForbidden();
      throw e;
    }
    renderTasks(tasks);
  }

  function memberEmail(userId) {
    const m = members.find((m) => m.id === userId);
    return m ? m.email : '알수없음';
  }

  function renderTasks(tasks) {
    ['TODO', 'DOING', 'DONE'].forEach((status) => {
      const col = $(`.kanban-col[data-status="${status}"]`);
      const list = col.querySelector('.task-list');
      const filtered = tasks.filter((t) => t.status === status);
      col.querySelector('.count').textContent = filtered.length;
      list.innerHTML = '';

      if (filtered.length === 0) {
        list.innerHTML = `<div class="text-center text-slate-400 dark:text-slate-500 text-sm py-6">카드 없음</div>`;
        return;
      }

      filtered.forEach((task) => {
        const card = document.createElement('div');
        card.className = 'kanban-card bg-white/80 dark:bg-white/[0.06] rounded-xl border border-black/5 dark:border-white/10 p-3 cursor-pointer';
        card.draggable = true;
        card.dataset.taskId = task.id;
        const assigneeLabel = task.assignee_id ? '@' + memberEmail(task.assignee_id).split('@')[0] : '⚠미할당';
        card.innerHTML = `
          <div class="font-medium text-slate-900 dark:text-slate-50">${escapeHtml(task.title)}</div>
          <div class="text-xs text-slate-400 dark:text-slate-500 mt-1">#${task.id} · ${assigneeLabel}</div>
        `;
        card.addEventListener('click', () => openTaskModal(task));
        card.addEventListener('dragstart', (e) => {
          e.dataTransfer.setData('text/plain', String(task.id));
        });
        list.appendChild(card);
      });
    });
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  $$('.kanban-col').forEach((col) => {
    col.addEventListener('dragover', (e) => e.preventDefault());
    col.addEventListener('drop', async (e) => {
      e.preventDefault();
      const taskId = e.dataTransfer.getData('text/plain');
      const status = col.dataset.status;
      try {
        await apiFetch(`/tasks/${taskId}/status`, {
          method: 'PATCH',
          body: JSON.stringify({ status }),
        });
        loadTasks();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  $$('.add-task-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const title = prompt('태스크 제목을 입력하세요');
      if (!title) return;
      try {
        await apiFetch(`/teams/${team.id}/tasks`, {
          method: 'POST',
          body: JSON.stringify({ title }),
        });
        loadTasks();
      } catch (err) {
        alert(err.message);
      }
    });
  });

  let modalTask = null;

  function openTaskModal(task) {
    modalTask = task;
    $('#modal-task-id').textContent = `#${task.id}`;
    $('#modal-title-display').textContent = '';
    $('#modal-title-input').value = task.title;
    $('#modal-error').textContent = '';

    $$('.modal-status-btn').forEach((b) => {
      b.classList.toggle('bg-[#0a84ff]', b.dataset.status === task.status);
      b.classList.toggle('text-white', b.dataset.status === task.status);
    });
    modalTask.selectedStatus = task.status;

    const select = $('#modal-assignee-select');
    select.innerHTML = '<option value="">미할당</option>';
    members.forEach((m) => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.email;
      if (task.assignee_id === m.id) opt.selected = true;
      select.appendChild(opt);
    });

    $('#task-modal').classList.remove('hidden');
  }

  $('#modal-close-btn').addEventListener('click', () => $('#task-modal').classList.add('hidden'));

  $$('.modal-status-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      modalTask.selectedStatus = btn.dataset.status;
      $$('.modal-status-btn').forEach((b) => {
        b.classList.toggle('bg-[#0a84ff]', b === btn);
        b.classList.toggle('text-white', b === btn);
      });
    });
  });

  $('#modal-save-btn').addEventListener('click', async () => {
    const errorBox = $('#modal-error');
    errorBox.textContent = '';
    const title = $('#modal-title-input').value;
    const assigneeVal = $('#modal-assignee-select').value;

    try {
      if (modalTask.selectedStatus !== modalTask.status) {
        await apiFetch(`/tasks/${modalTask.id}/status`, {
          method: 'PATCH',
          body: JSON.stringify({ status: modalTask.selectedStatus }),
        });
      }
      const payload = { title };
      if (assigneeVal === '') {
        payload.clear_assignee = true;
      } else {
        payload.assignee_id = Number(assigneeVal);
      }
      await apiFetch(`/tasks/${modalTask.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      });
      $('#task-modal').classList.add('hidden');
      loadTasks();
    } catch (err) {
      errorBox.textContent = err.message;
    }
  });

  $('#modal-delete-btn').addEventListener('click', () => {
    confirmAction('이 카드를 삭제하시겠습니까? 되돌릴 수 없습니다.', async () => {
      try {
        await apiFetch(`/tasks/${modalTask.id}`, { method: 'DELETE' });
        $('#task-modal').classList.add('hidden');
        loadTasks();
      } catch (err) {
        $('#modal-error').textContent = err.message;
      }
    });
  });

  function confirmAction(message, onConfirm) {
    $('#confirm-message').textContent = message;
    pendingDeleteHandler = onConfirm;
    $('#confirm-dialog').classList.remove('hidden');
  }
  $('#confirm-cancel-btn').addEventListener('click', () => $('#confirm-dialog').classList.add('hidden'));
  $('#confirm-ok-btn').addEventListener('click', async () => {
    $('#confirm-dialog').classList.add('hidden');
    if (pendingDeleteHandler) await pendingDeleteHandler();
  });

  // ---------- 채팅 ----------
  async function loadMessages() {
    const qs = lastMessageSince ? `?since=${encodeURIComponent(lastMessageSince)}` : '';
    let msgs;
    try {
      msgs = await apiFetch(`/teams/${team.id}/messages${qs}`);
    } catch (e) {
      if (e.code === 'FORBIDDEN') return showForbidden();
      $('#chat-status').textContent = '⚠ 연결 끊김 · 5초 후 재시도';
      $('#chat-status').className = 'text-xs text-red-600';
      return;
    }
    $('#chat-status').textContent = '● 5초마다 새로고침';
    $('#chat-status').className = 'text-xs text-emerald-600';

    if (msgs.length > 0) {
      lastMessageSince = msgs[msgs.length - 1].created_at;
      msgs.forEach(renderMessage);
      const box = $('#chat-messages');
      box.scrollTop = box.scrollHeight;
    }
  }

  function renderMessage(msg) {
    const box = $('#chat-messages');
    const mine = msg.user_id === currentUser.id;
    const wrap = document.createElement('div');
    wrap.className = mine ? 'text-right' : '';
    const time = (msg.created_at || '').slice(11, 16);
    const bubbleClass = mine
      ? 'text-white'
      : 'bg-black/5 dark:bg-white/10 text-slate-900 dark:text-slate-50';
    const bubbleStyle = mine ? 'background: linear-gradient(160deg,#1a93ff,#0a78ea);' : '';
    wrap.innerHTML = `
      <div class="text-xs text-slate-400 dark:text-slate-500">${escapeHtml(msg.user_email)} · ${time}</div>
      <div class="inline-block mt-1 px-3 py-2 rounded-2xl max-w-[80%] ${bubbleClass}" style="${bubbleStyle}">
        <span class="msg-content">${escapeHtml(msg.content)}</span>
        ${mine ? `<button class="msg-delete-btn ml-2 text-xs opacity-70" data-msg-id="${msg.id}">🗑</button>` : ''}
      </div>
    `;
    box.appendChild(wrap);

    if (mine) {
      wrap.querySelector('.msg-delete-btn').addEventListener('click', async () => {
        try {
          await apiFetch(`/messages/${msg.id}`, { method: 'DELETE' });
          wrap.remove();
        } catch (err) {
          alert(err.message);
        }
      });
    }
  }

  $('#chat-input').addEventListener('input', () => {
    $('#chat-count').textContent = $('#chat-input').value.length;
  });

  async function sendMessage() {
    const input = $('#chat-input');
    const content = input.value;
    const errorBox = $('#chat-error');
    errorBox.textContent = '';
    if (!content.trim()) return;
    if (content.length > 1000) {
      errorBox.textContent = '1000자 이내로 입력하세요';
      return;
    }
    try {
      await apiFetch(`/teams/${team.id}/messages`, {
        method: 'POST',
        body: JSON.stringify({ content }),
      });
      input.value = '';
      $('#chat-count').textContent = '0';
      loadMessages();
    } catch (err) {
      errorBox.textContent = err.message;
    }
  }
  $('#chat-send-btn').addEventListener('click', sendMessage);
  $('#chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // ---------- 멤버 ----------
  async function loadMembers() {
    try {
      members = await apiFetch(`/teams/${team.id}/members`);
    } catch (e) {
      if (e.code === 'FORBIDDEN') return showForbidden();
      throw e;
    }
    $('#member-count').textContent = members.length;
    const list = $('#member-list');
    list.innerHTML = '';
    members.forEach((m) => {
      const row = document.createElement('div');
      row.className = 'flex justify-between items-center px-4 py-3';
      row.innerHTML = `
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-full text-white flex items-center justify-center text-xs font-semibold" style="background: linear-gradient(160deg,#8e8ea0,#6e6e73);">${m.email[0].toUpperCase()}</div>
          <div class="text-sm text-slate-800 dark:text-slate-100">${escapeHtml(m.email)}${m.id === currentUser.id ? ' (나)' : ''}</div>
        </div>
        <span class="text-xs ${m.is_owner ? 'text-amber-500 font-bold' : 'text-slate-400 dark:text-slate-500'}">${m.is_owner ? '★ owner' : 'member'}</span>
      `;
      list.appendChild(row);
    });

    const isOwner = members.find((m) => m.id === currentUser.id)?.is_owner;
    const leaveBtn = $('#leave-team-btn');
    leaveBtn.disabled = isOwner;
    leaveBtn.classList.toggle('opacity-40', isOwner);
    leaveBtn.title = isOwner ? '팀 소유자는 탈퇴할 수 없습니다' : '';
  }

  $('#leave-team-btn').addEventListener('click', () => {
    confirmAction('정말 이 팀에서 탈퇴하시겠습니까?', async () => {
      try {
        await apiFetch(`/teams/${team.id}/leave`, { method: 'DELETE' });
        location.href = '/team-select.html';
      } catch (err) {
        $('#leave-error').textContent = err.message;
      }
    });
  });

  init();
})();
