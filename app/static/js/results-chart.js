/* Draw the saved solver trajectory; filtering never changes the calculation. */
(() => {
    const source = document.getElementById('chart-data');
    if (!source) return;
    const {times, trajectory, variables} = JSON.parse(source.textContent);
    const svg = document.getElementById('trajectory-chart');
    const legend = document.getElementById('chart-legend');
    const slider = document.getElementById('chart-time');
    const readout = document.getElementById('chart-readout');
    const palette = ['#cc7955','#607b55','#8e9d69','#87a0a1','#ba9e6c','#8686a3','#ac817e','#74a189','#adb97d','#7d8eaf','#be997f','#a6b2a7','#cead67','#9f8eaa','#799a70'];
    const active = new Set(variables.map((_, i) => i));
    const ns = 'http://www.w3.org/2000/svg';
    let width = 940, height = 330;
    const left = 58, right = 20, top = 24, bottom = 35;
    const first = times[0], last = times[times.length - 1];
    const x = t => left + ((t - first) / (last - first)) * (width - left - right);
    const number = value => new Intl.NumberFormat('ru-RU',{maximumSignificantDigits:5}).format(value);
    let pointer, yScale;
    const element = (tag, attrs = {}, text) => {
        const node = document.createElementNS(ns, tag);
        for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
        if (text !== undefined) node.textContent = text;
        return node;
    };
    const buttons = variables.map((v, i) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.setAttribute('aria-pressed','true');
        button.setAttribute('aria-label', `${v.symbol} — ${v.name}`);
        const dot = document.createElement('i');
        dot.style.backgroundColor = palette[i];
        button.append(dot, document.createTextNode(`${v.symbol} · ${v.name}`));
        button.addEventListener('click', () => {
            if (active.has(i)) active.delete(i); else active.add(i);
            draw();
        });
        legend.appendChild(button);
        return button;
    });
    const setMoment = index => {
        index = Math.max(0, Math.min(times.length - 1, index));
        slider.value = index;
        document.getElementById('chart-time-value').textContent = `t = ${number(times[index])}`;
        slider.setAttribute('aria-valuetext',`t = ${number(times[index])}`);
        readout.replaceChildren();
        if (pointer) {
            pointer.setAttribute('x1',x(times[index]));
            pointer.setAttribute('x2',x(times[index]));
        }
        // Values for every selected line remain available by keyboard and pointer.
        active.forEach(i => {
            const span = document.createElement('span');
            const label = document.createElement('strong');
            label.textContent = `${variables[i].symbol} `;
            label.style.color = palette[i];
            span.append(label,document.createTextNode(number(trajectory[index][i])));
            readout.appendChild(span);
        });
    };
    const draw = () => {
        width = Math.max(280, svg.clientWidth || 940);
        height = window.innerWidth < 600 ? 260 : 330;
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.replaceChildren();
        const selected = [...active];
        let min = Infinity, max = -Infinity;
        for (const row of trajectory) for (const i of selected) {
            min = Math.min(min,row[i]); max = Math.max(max,row[i]);
        }
        if (!selected.length) { min = 0; max = 1; }
        const padding = Math.max((max - min) * .13, Math.max(Math.abs(min),Math.abs(max),1) * .015);
        min -= padding; max += padding;
        yScale = value => top + ((max - value) / (max - min)) * (height - top - bottom);
        for (let tick = 0; tick <= 4; tick++) {
            const value = min + (max - min) * tick / 4;
            const yy = yScale(value);
            svg.append(element('line',{x1:left,y1:yy,x2:width-right,y2:yy,stroke:'#edf0e7','stroke-dasharray':'4 5'}));
            svg.append(element('text',{x:left-12,y:yy+4,'text-anchor':'end'},number(value)));
        }
        for (let tick = 0; tick <= 4; tick++) {
            const value = first + (last - first) * tick / 4;
            svg.append(element('text',{x:x(value),y:height-9,'text-anchor':'middle'},number(value)));
        }
        svg.append(element('text',{x:width-3,y:height-9,'text-anchor':'end'},'t'));
        svg.append(element('text',{x:left,y:12},'Lᵢ'));
        selected.forEach(i => {
            const path = trajectory.map((row, index) => `${index ? 'L' : 'M'}${x(times[index]).toFixed(2)},${yScale(row[i]).toFixed(2)}`).join(' ');
            svg.append(element('path',{d:path,fill:'none',stroke:palette[i],'stroke-width':2.4,'stroke-linecap':'round','stroke-linejoin':'round','data-series':i}));
        });
        if (!selected.length) svg.append(element('text',{x:width/2,y:height/2,'text-anchor':'middle'},'Выберите показатели под графиком'));
        pointer = element('line',{x1:left,y1:top,x2:left,y2:height-bottom,stroke:'#c7cfbe','stroke-width':1,'stroke-dasharray':'3 4'});
        svg.appendChild(pointer);
        buttons.forEach((button, i) => button.setAttribute('aria-pressed', String(active.has(i))));
        setMoment(Number(slider.value));
    };
    svg.addEventListener('pointermove', event => {
        const rect = svg.getBoundingClientRect();
        const px = (event.clientX - rect.left) / rect.width * width;
        const target = first + Math.max(0,Math.min(1,(px-left)/(width-left-right))) * (last-first);
        let low = 0, high = times.length - 1;
        while (low < high) {
            const mid = (low + high) >> 1;
            if (times[mid] < target) low = mid + 1; else high = mid;
        }
        if (low && target-times[low-1] < times[low]-target) low--;
        setMoment(low);
    });
    slider.addEventListener('input', () => setMoment(Number(slider.value)));
    document.getElementById('chart-show-all').addEventListener('click', () => {
        variables.forEach((_,i) => active.add(i)); draw();
    });
    document.getElementById('chart-finance').addEventListener('click', () => {
        active.clear(); [0,1,2,3].forEach(i => active.add(i)); draw();
    });
    document.getElementById('interactive-chart').hidden = false;
    draw();
    document.getElementById('chart-fallback').hidden = true;
    new ResizeObserver(() => {
        if (Math.abs(svg.clientWidth - width) > .5) draw();
    }).observe(svg.parentElement);
})();
