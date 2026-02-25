// Базовый URL API (бэкенд доступен на localhost:8000)
const API_BASE = 'https://glossary-backend-bzu2.onrender.com';

// Глобальные переменные для графа
let network = null;
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);

// ---------- Функции загрузки данных и построения графа ----------

/**
 * Загружает полную информацию обо всех терминах (связанные термины, источники)
 */
async function loadFullTerms() {
    try {
        // Сначала получаем список всех терминов (упрощённый)
        const listResponse = await fetch(`${API_BASE}/terms`);
        const simpleTerms = await listResponse.json();
        
        // Для каждого термина запрашиваем детальную информацию
        const fullTerms = await Promise.all(
            simpleTerms.map(t => fetch(`${API_BASE}/terms/${t.term}`).then(res => res.json()))
        );
        return fullTerms;
    } catch (error) {
        console.error('Ошибка загрузки полных данных:', error);
        return [];
    }
}

/**
 * Строит граф на основе полных данных терминов
 */
async function buildGraphFromFullTerms() {
    const fullTerms = await loadFullTerms();
    
    nodes.clear();
    edges.clear();
    
    // Добавляем узлы (каждый термин)
    const nodeItems = fullTerms.map(t => ({
        id: t.term,
        label: t.term,
        title: t.definition  // всплывающая подсказка
    }));
    nodes.add(nodeItems);
    
    // Добавляем рёбра на основе related_terms
    const edgeItems = [];
    fullTerms.forEach(t => {
        if (t.related_terms && Array.isArray(t.related_terms)) {
            t.related_terms.forEach(related => {
                edgeItems.push({
                    from: t.term,
                    to: related,
                    arrows: '' // без стрелок (ненаправленные связи)
                });
            });
        }
    });
    edges.add(edgeItems);
    
    // Если граф ещё не создан, создаём; иначе обновляем данные
    if (!network) {
        const container = document.getElementById('mynetwork');
        const data = { nodes, edges };
        const options = {
            layout: { improvedLayout: true },
            edges: { smooth: true },
            physics: { enabled: true }
        };
        network = new vis.Network(container, data, options);
        
        // Обработчик клика по узлу
        network.on('click', function(params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                showTermInfo(nodeId);
            }
        });
    } else {
        network.setData({ nodes, edges });
    }
}

// ---------- Отображение информации о термине ----------

/**
 * Загружает детальную информацию о термине и отображает в боковой панели
 * @param {string} term - название термина
 */
async function showTermInfo(term) {
    try {
        const response = await fetch(`${API_BASE}/terms/${term}`);
        const data = await response.json();
        displayInfo(data);
        fillForm(data); // заполняем форму для возможного редактирования
    } catch (error) {
        console.error('Ошибка загрузки информации о термине:', error);
    }
}

/**
 * Отображает информацию о термине в блоке #info
 * @param {Object} term - объект термина (полные данные)
 */
function displayInfo(term) {
    const infoDiv = document.getElementById('info');
    let sourcesHtml = '';
    if (term.sources && term.sources.length) {
        sourcesHtml = '<ul>' + term.sources.map(s => `<li><a href="${s}" target="_blank">${s}</a></li>`).join('') + '</ul>';
    } else {
        sourcesHtml = '<p>Нет источников</p>';
    }
    infoDiv.innerHTML = `
        <h3>${term.term}</h3>
        <p><strong>Определение:</strong> ${term.definition}</p>
        <p><strong>Источники:</strong></p>
        ${sourcesHtml}
        <p><strong>Связанные термины:</strong> ${term.related_terms ? term.related_terms.join(', ') : ''}</p>
    `;
}

// ---------- Работа с формой ----------

/**
 * Заполняет форму данными термина (для редактирования)
 * @param {Object} term - объект термина
 */
function fillForm(term) {
    document.getElementById('original-term').value = term.term;
    document.getElementById('term').value = term.term;
    document.getElementById('definition').value = term.definition;
    document.getElementById('sources').value = term.sources ? term.sources.join(', ') : '';
    document.getElementById('related').value = term.related_terms ? term.related_terms.join(', ') : '';
}

/**
 * Очищает форму
 */
function clearForm() {
    document.getElementById('original-term').value = '';
    document.getElementById('term').value = '';
    document.getElementById('definition').value = '';
    document.getElementById('sources').value = '';
    document.getElementById('related').value = '';
}

// ---------- Обработчики кнопок ----------

// document.getElementById('add-btn').addEventListener('click', async () => {
//     const termInput = document.getElementById('term').value.trim();
//     if (!termInput) {
//         alert('Термин обязателен');
//         return;
//     }
//     const data = {
//         term: termInput,
//         definition: document.getElementById('definition').value.trim(),
//         sources: document.getElementById('sources').value.split(',').map(s => s.trim()).filter(s => s),
//         related_terms: document.getElementById('related').value.split(',').map(s => s.trim()).filter(s => s)
//     };
//     try {
//         const response = await fetch(`${API_BASE}/terms`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(data)
//         });
//         if (!response.ok) {
//             const err = await response.json();
//             alert('Ошибка: ' + err.detail);
//             return;
//         }
//         clearForm();
//         buildGraphFromFullTerms(); // перестраиваем граф
//     } catch (error) {
//         alert('Ошибка соединения');
//     }
// });

// document.getElementById('update-btn').addEventListener('click', async () => {
//     const originalTerm = document.getElementById('original-term').value;
//     if (!originalTerm) {
//         alert('Выберите термин для обновления');
//         return;
//     }
//     const termInput = document.getElementById('term').value.trim();
//     if (!termInput) {
//         alert('Термин обязателен');
//         return;
//     }
//     const data = {
//         term: termInput,
//         definition: document.getElementById('definition').value.trim(),
//         sources: document.getElementById('sources').value.split(',').map(s => s.trim()).filter(s => s),
//         related_terms: document.getElementById('related').value.split(',').map(s => s.trim()).filter(s => s)
//     };
//     try {
//         const response = await fetch(`${API_BASE}/terms/${originalTerm}`, {
//             method: 'PUT',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(data)
//         });
//         if (!response.ok) {
//             const err = await response.json();
//             alert('Ошибка: ' + err.detail);
//             return;
//         }
//         clearForm();
//         buildGraphFromFullTerms();
//     } catch (error) {
//         alert('Ошибка соединения');
//     }
// });

// document.getElementById('delete-btn').addEventListener('click', async () => {
//     const originalTerm = document.getElementById('original-term').value;
//     if (!originalTerm) {
//         alert('Выберите термин для удаления');
//         return;
//     }
//     if (!confirm(`Удалить термин "${originalTerm}"?`)) return;
//     try {
//         const response = await fetch(`${API_BASE}/terms/${originalTerm}`, {
//             method: 'DELETE'
//         });
//         if (!response.ok) {
//             const err = await response.json();
//             alert('Ошибка: ' + err.detail);
//             return;
//         }
//         clearForm();
//         buildGraphFromFullTerms();
//     } catch (error) {
//         alert('Ошибка соединения');
//     }
// });

// document.getElementById('clear-btn').addEventListener('click', clearForm);

// Запуск: загружаем граф при загрузке страницы
window.addEventListener('load', () => {
    buildGraphFromFullTerms();
});