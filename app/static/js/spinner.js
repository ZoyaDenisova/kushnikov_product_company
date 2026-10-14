const form = document.getElementById('company-form');
if (form) {
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
    form.addEventListener('input', progress);
    updateDegree();
    const stepBody = document.querySelector('#q4-table tbody');
    const renumberSteps = () => stepBody.querySelectorAll('tr').forEach((row,i) => {
        const inputs = row.querySelectorAll('input');
        inputs[0].name = `q4_time_${i}`;
        inputs[0].setAttribute('aria-label',`q4 время ${i+1}`);
        inputs[1].name = `q4_value_${i}`;
        inputs[1].setAttribute('aria-label',`q4 уровень ${i+1}`);
    });
    document.getElementById('add-step').addEventListener('click', () => {
        const row = document.createElement('tr');
        row.innerHTML = '<td><input type="number" step="any" min="0" required></td><td><input type="number" step="any" required></td><td><button type="button" class="btn btn-outline-secondary remove-step">Удалить</button></td>';
        stepBody.appendChild(row);
        renumberSteps();
    });
    stepBody.addEventListener('click', event => {
        if (event.target.classList.contains('remove-step')) {
            event.target.closest('tr').remove();
            renumberSteps();
        }
    });
    form.addEventListener('invalid', event => {
        let parent = event.target.parentElement;
        while (parent) {
            if (parent.tagName === 'DETAILS') parent.open = true;
            parent = parent.parentElement;
        }
    }, true);
    form.addEventListener('submit', () => {
        document.getElementById('spinner').style.display = 'inline';
        form.querySelectorAll('button[type=submit]').forEach(button => button.disabled = true);
    });
    window.addEventListener('pageshow', () => {
        document.getElementById('spinner').style.display = 'none';
        form.querySelectorAll('button[type=submit]').forEach(button => button.disabled = false);
    });
}
