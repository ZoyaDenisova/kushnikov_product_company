/* Progressive enhancement: all form sections remain available without JavaScript. */
const form = document.getElementById('company-form');
if (form) {
    const coefficientMeasure = document.createElement('canvas').getContext('2d');
    const fitCoefficient = (input, event) => {
        if (!input.matches('.coefficient-square')) return;
        const style = getComputedStyle(input);
        coefficientMeasure.font = `${style.fontStyle} ${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
        const height = parseFloat(style.height);
        // Keep incomplete negative/exponential input from collapsing mid-entry.
        if (input.validity.badInput) {
            if (event?.inputType?.startsWith('insert')) {
                const extra = coefficientMeasure.measureText(event.data || '0').width;
                input.style.width = `${Math.max(height, parseFloat(input.style.width) || height) + extra}px`;
            }
            return;
        }
        const textWidth = coefficientMeasure.measureText(input.value.replace('.', ',')).width;
        const frame = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight) +
            parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth);
        input.style.width = `${Math.max(height, Math.ceil(textWidth + frame + 4))}px`;
    };
    const fitCoefficients = () => form.querySelectorAll('.coefficient-square').forEach(input => fitCoefficient(input));
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
    const progress = () => {
        let completed = 0;
        form.querySelectorAll('.coefficient-group').forEach(group => {
            const fields = [...group.querySelectorAll('[data-coefficient]')].filter(input => !input.disabled);
            const filled = fields.filter(input => input.value !== '' && input.validity.valid).length;
            group.querySelector('.group-progress').textContent = `${filled}/${fields.length} коэффициентов`;
            completed += filled;
        });
        const count = 98 * 4;
        document.getElementById('coefficient-progress').textContent = `${completed}/${count} коэффициентов`;
    };
    form.addEventListener('input', event => {
        event.target.classList.remove('user-invalid');
        fitCoefficient(event.target, event);
        progress();
    });
    progress();
    const randomButton = document.getElementById('randomize-all');
    randomButton.addEventListener('click', async () => {
        const status = document.getElementById('randomize-status');
        const intervalStart = form.elements.namedItem('t_start').value;
        const intervalEnd = form.elements.namedItem('t_end').value;
        randomButton.disabled = true;
        status.textContent = 'Заполняем случайные значения...';
        try {
            const response = await fetch(randomButton.dataset.randomUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    t_start: intervalStart, t_end: intervalEnd,
                    polynomial_degree: 3,
                }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error);
            if (intervalStart !== form.elements.namedItem('t_start').value ||
                intervalEnd !== form.elements.namedItem('t_end').value) {
                throw new Error('Настройки изменились во время заполнения. Повторите генерацию.');
            }
            for (const [name, value] of Object.entries(data.values)) {
                if (name !== 't_start' && name !== 't_end') form.elements.namedItem(name).value = value;
            }
            fitCoefficients();
            form.querySelectorAll('.user-invalid').forEach(input => input.classList.remove('user-invalid'));
            progress();
            status.textContent = 'Все разделы заполнены случайными значениями.';
        } catch (error) {
            status.textContent = error.message || 'Не удалось сгенерировать параметры. Попробуйте ещё раз.';
        } finally {
            randomButton.disabled = false;
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
        fitCoefficients();
        form.removeAttribute('aria-busy');
        document.getElementById('spinner').style.display = 'none';
        form.querySelectorAll('button[type=submit]').forEach(button => button.disabled = false);
    });
    window.addEventListener('resize', fitCoefficients);
    fitCoefficients();
}
