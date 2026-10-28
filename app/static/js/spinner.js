/* Progressive enhancement: all form sections remain available without JavaScript. */
const form = document.getElementById('company-form');
if (form) {
    const tabs = [...form.querySelectorAll('[data-tab]')];
    const panels = [...form.querySelectorAll('.tab-panel')];
    const activateTab = (id, focus = false) => {
        tabs.forEach(tab => {
            const active = tab.dataset.tab === id;
            tab.setAttribute('aria-selected', String(active));
            tab.tabIndex = active ? 0 : -1;
            if (active && focus) tab.focus();
        });
        panels.forEach(panel => panel.hidden = panel.id !== id);
    };
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => activateTab(tab.dataset.tab));
        tab.addEventListener('keydown', event => {
            let next;
            if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
            if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
            if (event.key === 'Home') next = 0;
            if (event.key === 'End') next = tabs.length - 1;
            if (next === undefined) return;
            event.preventDefault();
            activateTab(tabs[next].dataset.tab, true);
        });
    });
    form.querySelectorAll('[data-go-tab]').forEach(button => button.addEventListener('click', () => {
        activateTab(button.dataset.goTab, true);
        form.querySelector('.form-tabs').scrollIntoView({block:'start',behavior:'smooth'});
    }));
    activateTab('indicators');
    const degree = document.getElementById('polynomial_degree');
    const progress = () => {
        let completed = 0;
        form.querySelectorAll('.coefficient-group').forEach(group => {
            const fields = [...group.querySelectorAll('[data-coefficient]')].filter(input => !input.disabled);
            const filled = fields.filter(input => input.value !== '' && input.validity.valid).length;
            group.querySelector('.group-progress').textContent = `${filled}/${fields.length} коэффициентов`;
            completed += filled;
        });
        const count = degree.value === '' ? 0 : 98 * (Number(degree.value) + 1);
        document.getElementById('coefficient-progress').textContent = `${completed}/${count} коэффициентов`;
    };
    const updateDegree = () => {
        const chosen = degree.value !== '';
        document.getElementById('coefficient-groups').hidden = !chosen;
        document.getElementById('choose-degree-note').hidden = chosen;
        form.querySelectorAll('[data-degree]').forEach(cell => {
            const hidden = !chosen || Number(cell.dataset.degree) > Number(degree.value);
            cell.hidden = hidden;
            cell.querySelectorAll('input').forEach(input => input.disabled = hidden);
        });
        progress();
    };
    degree.addEventListener('change', updateDegree);
    form.addEventListener('input', event => {
        event.target.classList.remove('user-invalid');
        progress();
    });
    updateDegree();
    const stepBody = document.querySelector('#q4-table tbody');
    const renumberSteps = () => stepBody.querySelectorAll('tr').forEach((row, i) => {
        const inputs = row.querySelectorAll('input');
        inputs[0].name = `q4_time_${i}`;
        inputs[0].setAttribute('aria-label', `q4 время ${i+1}`);
        inputs[1].name = `q4_value_${i}`;
        inputs[1].setAttribute('aria-label', `q4 уровень ${i+1}`);
    });
    document.getElementById('randomize-all').addEventListener('click', () => {
        const random = (low, high, decimals = 3) =>
            Number((low + Math.random() * (high - low)).toFixed(decimals));
        const set = (name, value) => { form.elements.namedItem(name).value = value; };

        form.querySelectorAll('#indicators input[name$="_scale"]').forEach(input => {
            const symbol = input.name.replace('_scale', '');
            set(symbol, random(.40, .85));
            set(symbol + '_scale', random(5, 15, 1));
            set(symbol + '_minimum', random(.10, .35));
        });

        for (const [factor, offset, amplitude] of [
            ['q1', [.25, .50], [.03, .15]],
            ['q2', [.15, .40], [.02, .10]],
        ]) {
            set(factor + '_a', random(...offset));
            set(factor + '_b', random(...amplitude));
            set(factor + '_c', random(Math.PI, 4 * Math.PI));
            set(factor + '_d', random(0, 2 * Math.PI));
        }
        set('q5_a', random(.05, .20));
        set('q5_b', random(.25, .60));

        // Preserve the step count and keep the fixed first transition at t=0.
        const steps = [...stepBody.querySelectorAll('tr')];
        const end = Number(form.elements.namedItem('t_end').value);
        const horizon = Number.isFinite(end) ? Math.max(1, end) : 1;
        steps.forEach((row, i) => {
            const time = i === 0 ? 0 : Number((
                horizon * ((i + random(-.3, .3)) / steps.length)
            ).toPrecision(12));
            const fields = row.querySelectorAll('input');
            fields[0].value = time;
            fields[1].value = random(.03, .25);
        });

        if (degree.value === '') degree.value = '2';
        const ranges = [[.75, .95], [.10, .25], [-.025, .05], [-.01, .02]];
        form.querySelectorAll('[data-coefficient]').forEach(input => {
            input.value = random(...ranges[Number(input.dataset.coefficient)]);
        });
        form.querySelectorAll('.user-invalid').forEach(input => input.classList.remove('user-invalid'));
        updateDegree();
        document.getElementById('randomize-status').textContent =
            'Показатели, внешние факторы и все 98 функций заполнены.';
    });
    document.getElementById('add-step').addEventListener('click', () => {
        const row = document.createElement('tr');
        row.innerHTML = '<td><input type="number" step="any" min="0" required></td><td><input type="number" step="any" required></td><td><button type="button" class="btn btn-quiet remove-step">Удалить</button></td>';
        stepBody.appendChild(row);
        renumberSteps();
        row.querySelector('input').focus();
    });
    stepBody.addEventListener('click', event => {
        const button = event.target.closest('.remove-step');
        if (button) {
            button.closest('tr').remove();
            renumberSteps();
            document.getElementById('add-step').focus();
        }
    });
    // The first invalid field selects its tab before native validation focuses it.
    let handlingInvalid = false;
    form.addEventListener('invalid', event => {
        event.target.classList.add('user-invalid');
        if (handlingInvalid) return;
        handlingInvalid = true;
        queueMicrotask(() => handlingInvalid = false);
        const panel = event.target.closest('.tab-panel');
        if (panel) activateTab(panel.id);
        let parent = event.target.parentElement;
        while (parent) {
            if (parent.tagName === 'DETAILS') parent.open = true;
            parent = parent.parentElement;
        }
    }, true);
    form.addEventListener('submit', () => {
        form.setAttribute('aria-busy', 'true');
        document.getElementById('spinner').style.display = 'inline';
        form.querySelectorAll('button[type=submit]').forEach(button => button.disabled = true);
    });
    window.addEventListener('pageshow', () => {
        form.removeAttribute('aria-busy');
        document.getElementById('spinner').style.display = 'none';
        form.querySelectorAll('button[type=submit]').forEach(button => button.disabled = false);
    });
}
