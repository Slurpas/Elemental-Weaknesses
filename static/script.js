// DOM elements
const pokemonSearch = document.getElementById('pokemonSearch');
const searchBtn = document.getElementById('searchBtn');
const searchResults = document.getElementById('searchResults');
const pokemonInfo = document.getElementById('pokemonInfo');
const loading = document.getElementById('loading');
const error = document.getElementById('error');

// Team management
let userTeam = [];
let currentOpponent = null;

// Tab functionality
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');

// Search functionality
let searchTimeout;

// Modal team selection
let currentTeamSlot = null;
const teamModal = document.getElementById('teamModal');
const teamModalSearch = document.getElementById('teamModalSearch');
const teamModalResults = document.getElementById('teamModalResults');
const closeTeamModalBtn = document.getElementById('closeTeamModal');

// Battle Simulator State
let battleState = {
    pokemon1: null,
    pokemon2: null,
    pokemon1Moves: null,
    pokemon2Moves: null
};

// Battle Modal State
let battleModalState = {
    isOpen: false,
    selectingFor: null // 'pokemon1' or 'pokemon2'
};

pokemonSearch.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();
    
    if (query.length < 1) {
        searchResults.style.display = 'none';
        return;
    }
    
    searchTimeout = setTimeout(() => {
        searchPokemon(query);
    }, 150);
});

searchBtn.addEventListener('click', () => {
    const query = pokemonSearch.value.trim();
    if (query) {
        getPokemonData(query);
    }
});

pokemonSearch.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const query = pokemonSearch.value.trim();
        if (query) {
            getPokemonData(query);
        }
    }
});

// Tab switching
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        
        // Update active tab button
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active tab pane
        tabPanes.forEach(pane => {
            pane.classList.remove('active');
            if (pane.id === targetTab) {
                pane.classList.add('active');
            }
        });
    });
});

async function searchPokemon(query) {
    try {
        const response = await fetch(`/api/search/${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.error) {
            searchResults.style.display = 'none';
            return;
        }
        
        displaySearchResults(data);
    } catch (error) {
        console.error('Search error:', error);
        searchResults.style.display = 'none';
    }
}

function displaySearchResults(pokemonList) {
    if (pokemonList.length === 0) {
        searchResults.style.display = 'none';
        return;
    }
    
    searchResults.innerHTML = pokemonList
        .map(pokemon => `
            <div class="search-result-item" onclick="selectPokemon('${pokemon.name}')">
                ${pokemon.readable_name || (pokemon.name.charAt(0).toUpperCase() + pokemon.name.slice(1))}
            </div>
        `)
        .join('');
    
    searchResults.style.display = 'block';
}

function selectPokemon(name) {
    pokemonSearch.value = name;
    searchResults.style.display = 'none';
    getPokemonData(name);
}

async function getPokemonData(name) {
    showLoading();
    hideError();
    hidePokemonInfo();
    
    try {
        const response = await fetch(`/api/pokemon/${encodeURIComponent(name)}`);
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        displayPokemonInfo(data);
    } catch (error) {
        console.error('Error fetching Pokemon data:', error);
        showError('Failed to fetch Pokemon data');
    } finally {
        hideLoading();
    }
}

function displayPokemonInfo(pokemon) {
    currentOpponent = pokemon;
    document.getElementById('pokemonSprite').src = pokemon.sprite;
    document.getElementById('pokemonName').textContent = pokemon.name.charAt(0).toUpperCase() + pokemon.name.slice(1);
    const typesContainer = document.getElementById('pokemonTypes');
    typesContainer.innerHTML = pokemon.types.map(type => `<span class="type-badge type-${type}">${type}</span>`).join('');
    document.getElementById('pokemonHP').textContent = `HP: ${pokemon.stats.hp}`;
    document.getElementById('pokemonAttack').textContent = `ATK: ${pokemon.stats.attack}`;
    document.getElementById('pokemonDefense').textContent = `DEF: ${pokemon.stats.defense}`;
    displayEffectiveness(pokemon.effectiveness);
    showPokemonInfo();
    if (userTeam.length > 0) {
        updateTeamAnalysis();
    }
    onSelectionChange();
}

function displayEffectiveness(effectiveness) {
    // Weaknesses
    const weaknessesList = document.getElementById('weaknessesList');
    weaknessesList.innerHTML = effectiveness.weaknesses.length > 0 
        ? effectiveness.weaknesses
            .map(([type, mult]) => `<span class="type-badge type-${type} weakness">${type} (${mult}x)</span>`)
            .join('')
        : '<span class="no-data">None</span>';
    
    // Resistances
    const resistancesList = document.getElementById('resistancesList');
    resistancesList.innerHTML = effectiveness.resistances.length > 0
        ? effectiveness.resistances
            .map(([type, mult]) => `<span class="type-badge type-${type} resistance">${type} (${mult}x)</span>`)
            .join('')
        : '<span class="no-data">None</span>';
    
    // Immunities
    const immunitiesList = document.getElementById('immunitiesList');
    immunitiesList.innerHTML = effectiveness.immunities.length > 0
        ? effectiveness.immunities
            .map(([type, mult]) => `<span class="type-badge type-${type} immunity">${type} (${mult}x)</span>`)
            .join('')
        : '<span class="no-data">None</span>';
}

function displayMoves(pvpMoves) {
    const movesList = document.getElementById('movesList');
    let html = '';
    if (pvpMoves && pvpMoves.length > 0) {
        html += `<div class="moves-pvp-header">Top PvP Moves</div>`;
        html += `<div class="moves-list-pvp">`;
        html += pvpMoves.map(move => {
            let effClass = '';
            if (move.effectiveness) {
                if (move.effectiveness.label === 'Super Effective') effClass = 'move-eff-super';
                else if (move.effectiveness.label === 'Not Very Effective') effClass = 'move-eff-notvery';
                else if (move.effectiveness.label === 'Immune') effClass = 'move-eff-immune';
                else effClass = 'move-eff-neutral';
            }
            return `
            <div class="move-item">
                <div class="move-info">
                    <span class="move-name">${move.name}</span>
                    <span class="type-badge type-${move.type}">${move.type}</span>
                    <span class="move-type">(${move.move_class === 'fast' ? 'Fast Move' : 'Charged Move'})</span>
                    <span class="move-effectiveness ${effClass}">${move.effectiveness ? move.effectiveness.label : ''}</span>
                </div>
            </div>
            `;
        }).join('');
        html += `</div>`;
    } else {
        html += '<div class="no-data">No PvP moves found</div>';
    }
    movesList.innerHTML = html;
}

// UI helper functions
function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function showError(message) {
    error.querySelector('p').textContent = message;
    error.classList.remove('hidden');
}

function hideError() {
    error.classList.add('hidden');
}

function showPokemonInfo() {
    pokemonInfo.classList.remove('hidden');
}

function hidePokemonInfo() {
    pokemonInfo.classList.add('hidden');
}

// Open modal when a team slot is clicked
function openTeamSlot(slotNumber) {
    currentTeamSlot = slotNumber;
    teamModal.classList.remove('hidden');
    teamModalSearch.value = '';
    teamModalResults.innerHTML = '';
    teamModalSearch.focus();
}

// Close modal
function closeTeamModal() {
    teamModal.classList.add('hidden');
    currentTeamSlot = null;
}

closeTeamModalBtn.addEventListener('click', closeTeamModal);
teamModal.addEventListener('click', (e) => {
    if (e.target === teamModal) closeTeamModal();
});
document.addEventListener('keydown', (e) => {
    if (!teamModal.classList.contains('hidden') && e.key === 'Escape') closeTeamModal();
});

// Search in modal
let teamModalSearchTimeout;
teamModalSearch.addEventListener('input', (e) => {
    clearTimeout(teamModalSearchTimeout);
    const query = e.target.value.trim();
    if (query.length < 2) {
        teamModalResults.innerHTML = '';
        return;
    }
    teamModalSearchTimeout = setTimeout(() => {
        fetch(`/api/search/${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    teamModalResults.innerHTML = '';
                    return;
                }
                teamModalResults.innerHTML = data.map(pokemon => `
                    <div class="modal-result-item" onclick="window.selectTeamPokemonModal('${pokemon.name}')">
                        <img class="modal-result-sprite" src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${getSpriteId(pokemon.name)}.png" alt="${pokemon.readable_name}" onerror="this.onerror=null;this.src='${placeholderSprite}';">
                        <span class="modal-result-name">${pokemon.readable_name || (pokemon.name.charAt(0).toUpperCase() + pokemon.name.slice(1))}</span>
                    </div>
                `).join('');
            });
    }, 150);
});

// Helper to get sprite id from name (works for most forms)
function getSpriteId(name) {
    return name;
}

const placeholderSprite = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png';

window.selectTeamPokemonModal = function(pokemonName) {
    addPokemonToTeam(pokemonName, currentTeamSlot);
    closeTeamModal();
};

async function addPokemonToTeam(pokemonName, slotNumber) {
    try {
        const response = await fetch(`/api/pokemon/${encodeURIComponent(pokemonName)}`);
        const data = await response.json();
        
        if (data.error) {
            alert(`Pokemon not found: ${pokemonName}`);
            return;
        }
        
        // Add to team
        const teamMember = {
            slot: slotNumber,
            name: data.name,
            sprite: data.sprite,
            types: data.types,
            effectiveness: data.effectiveness,
            pvp_moves: data.pvp_moves || []
        };
        
        // Remove existing Pokemon in this slot
        userTeam = userTeam.filter(p => p.slot !== slotNumber);
        userTeam.push(teamMember);
        
        // Update UI
        updateTeamSlot(slotNumber, teamMember);
        updateTeamAnalysis();
        
    } catch (error) {
        console.error('Error adding Pokemon to team:', error);
        alert('Failed to add Pokemon to team');
    }
    onSelectionChange();
}

function updateTeamSlot(slotNumber, pokemon, movesEffectiveness = null, isBestCounter = false) {
    const slot = document.querySelector(`[data-slot="${slotNumber}"]`);
    slot.classList.add('filled');
    
    // Add or remove best counter class for bold border
    if (isBestCounter) {
        slot.classList.add('best-counter');
    } else {
        slot.classList.remove('best-counter');
    }
    
    // Generate moves HTML if PvP moves exist
    let movesHTML = '';
    if (pokemon.pvp_moves && pokemon.pvp_moves.length > 0) {
        movesHTML = `
            <div class="team-moves-section">
                <h4>PvP Moves</h4>
                <div class="team-moves-list">
                    ${pokemon.pvp_moves.map(move => {
                        let effectivenessHTML = '';
                        if (movesEffectiveness && currentOpponent) {
                            const moveEffectiveness = movesEffectiveness.find(m => m.move.name === move.name);
                            if (moveEffectiveness) {
                                let effClass = '';
                                if (moveEffectiveness.effectiveness.label === 'Super Effective') effClass = 'move-eff-super';
                                else if (moveEffectiveness.effectiveness.label === 'Not Very Effective') effClass = 'move-eff-notvery';
                                else if (moveEffectiveness.effectiveness.label === 'Immune') effClass = 'move-eff-immune';
                                else effClass = 'move-eff-neutral';
                                effectivenessHTML = `<span class="move-effectiveness ${effClass}">${moveEffectiveness.effectiveness.label}</span>`;
                            }
                        }
                        
                        return `
                            <div class="move-item">
                                <div class="move-info">
                                    <div class="move-name">${move.name}</div>
                                    <div class="move-details">
                                        <span class="type-badge type-${move.type}">${move.type}</span>
                                        <span class="move-type">(${move.move_class === 'fast' ? 'Fast Move' : 'Charged Move'})</span>
                                        ${effectivenessHTML}
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    slot.innerHTML = `
        <div class="slot-content">
            <div class="pokemon-in-slot">
                <div class="pokemon-left-section">
                    <div class="pokemon-name">${pokemon.name}</div>
                    <img src="${pokemon.sprite}" alt="${pokemon.name}">
                    <div class="pokemon-types">
                        ${pokemon.types.map(type => `<span class="type-badge type-${type}">${type}</span>`).join('')}
                    </div>
                </div>
                <div class="pokemon-right-section">
                    ${movesHTML}
                </div>
                <button class="remove-pokemon" onclick="removePokemonFromTeam('${slotNumber}')">×</button>
            </div>
        </div>
    `;
}

function removePokemonFromTeam(slotNumber) {
    userTeam = userTeam.filter(p => p.slot !== slotNumber);
    
    const slot = document.querySelector(`[data-slot="${slotNumber}"]`);
    slot.classList.remove('filled');
    slot.innerHTML = `
        <div class="slot-content">
            <div class="add-pokemon">
                <span class="plus-icon">+</span>
                <span class="add-text">Add Pokemon</span>
            </div>
        </div>
    `;
    
    updateTeamAnalysis();
    onSelectionChange();
}

function updateTeamAnalysis() {
    const teamAnalysis = document.getElementById('teamAnalysis');
    
    if (userTeam.length === 0) {
        teamAnalysis.classList.add('hidden');
        return;
    }
    
    teamAnalysis.classList.remove('hidden');
    
    // Calculate team coverage
    const coverage = calculateTeamCoverage();
    displayTeamCoverage(coverage);
    
    // Show matchups if there's a current opponent
    if (currentOpponent) {
        displayTeamMatchups();
    }
}

function calculateTeamCoverage() {
    const coverage = {};
    const allTypes = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 
                     'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 
                     'dragon', 'dark', 'steel', 'fairy'];
    
    // Initialize coverage
    allTypes.forEach(type => {
        coverage[type] = { count: 0, pokemon: [] };
    });
    
    // Count how many Pokemon can hit each type effectively
    userTeam.forEach(pokemon => {
        if (pokemon.effectiveness && pokemon.effectiveness.effectiveness) {
            Object.entries(pokemon.effectiveness.effectiveness).forEach(([type, multiplier]) => {
                if (multiplier > 1) {
                    coverage[type].count++;
                    coverage[type].pokemon.push(pokemon.name);
                }
            });
        }
    });
    
    return coverage;
}

function displayTeamCoverage(coverage) {
    const coverageGrid = document.getElementById('teamCoverage');
    
    const coverageHTML = Object.entries(coverage)
        .filter(([type, data]) => data.count > 0)
        .sort((a, b) => b[1].count - a[1].count)
        .map(([type, data]) => `
            <div class="coverage-item">
                <span class="type-badge type-${type}">${type}</span>
                <span class="coverage-count">${data.count}</span>
            </div>
        `).join('');
    
    coverageGrid.innerHTML = coverageHTML || '<div class="no-data">No coverage data</div>';
}

function displayTeamMatchups() {
    if (!currentOpponent) return;
    
    const matchupList = document.getElementById('teamMatchups');
    
    const matchups = userTeam.map(pokemon => {
        const effectiveness = currentOpponent.effectiveness.effectiveness[pokemon.types[0]] || 1;
        let effectivenessClass = 'neutral';
        let effectivenessText = `${effectiveness}x`;
        
        if (effectiveness > 1) {
            effectivenessClass = 'bad';
        } else if (effectiveness < 1) {
            effectivenessClass = 'good';
        }
        
        return {
            pokemon: pokemon.name,
            effectiveness: effectiveness,
            effectivenessClass: effectivenessClass,
            effectivenessText: effectivenessText
        };
    });
    
    const matchupHTML = matchups.map(matchup => `
        <div class="matchup-item">
            <span class="matchup-pokemon">${matchup.pokemon}</span>
            <span class="matchup-effectiveness ${matchup.effectivenessClass}">${matchup.effectivenessText}</span>
        </div>
    `).join('');
    
    matchupList.innerHTML = matchupHTML;
}

// Close search results when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-section')) {
        searchResults.style.display = 'none';
    }
});

// Add some CSS for the no-data class
const style = document.createElement('style');
style.textContent = `
    .no-data {
        color: #999;
        font-style: italic;
        padding: 10px;
    }
`;
document.head.appendChild(style);

document.querySelector('.team-slots').addEventListener('click', (e) => {
    const slot = e.target.closest('.team-slot');
    if (slot) {
        const slotNumber = slot.dataset.slot;
        openTeamSlot(slotNumber);
    }
});

// --- MATCHUP INTEGRATION ---
async function updateMatchupAnalysis() {
    // Only run if we have an opponent and at least one team member
    if (!currentOpponent || userTeam.length === 0) return;
    const opponentName = currentOpponent.name;
    const teamNames = userTeam.map(p => p.name);
    try {
        const resp = await fetch('/api/matchup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ opponent: opponentName, team: teamNames })
        });
        const data = await resp.json();
        renderOpponentMovesVsTeam(data.opponent_moves_vs_team, data.team);
        updateAllTeamSlotsWithEffectiveness(data.team_moves_vs_opponent);
    } catch (e) {
        console.error('Failed to fetch matchup analysis:', e);
    }
}

function updateAllTeamSlotsWithEffectiveness(teamMovesVsOpponent) {
    // Calculate scores for each team member
    const teamScores = calculateTeamScores(teamMovesVsOpponent);
    
    // Find the best score(s)
    const bestScore = Math.max(...teamScores.map(score => score.totalScore));
    const bestPokemon = teamScores.filter(score => score.totalScore === bestScore);
    
    userTeam.forEach(pokemon => {
        const movesEffectiveness = teamMovesVsOpponent.find(t => t.pokemon === pokemon.name);
        const isBestCounter = bestPokemon.some(best => best.pokemonName === pokemon.name);
        
        if (movesEffectiveness) {
            updateTeamSlot(pokemon.slot, pokemon, movesEffectiveness.moves, isBestCounter);
        } else {
            updateTeamSlot(pokemon.slot, pokemon, null, isBestCounter);
        }
    });
}

function calculateTeamScores(teamMovesVsOpponent) {
    const scores = [];
    
    userTeam.forEach(pokemon => {
        const movesEffectiveness = teamMovesVsOpponent.find(t => t.pokemon === pokemon.name);
        if (!movesEffectiveness) return;
        
        // Calculate offensive score (your moves vs opponent)
        let offensiveScore = 0;
        let bestFastScore = -Infinity;
        let bestChargedScore = -Infinity;
        
        movesEffectiveness.moves.forEach(move => {
            let moveScore = 0;
            if (move.effectiveness.label === 'Super Effective') {
                moveScore = move.move.move_class === 'fast' ? 2 : 5;
            } else if (move.effectiveness.label === 'Not Very Effective') {
                moveScore = move.move.move_class === 'fast' ? -1 : -3;
            } else if (move.effectiveness.label === 'Immune') {
                moveScore = move.move.move_class === 'fast' ? -2 : -5;
            }
            // Neutral = 0
            
            if (move.move.move_class === 'fast') {
                bestFastScore = Math.max(bestFastScore, moveScore);
            } else {
                bestChargedScore = Math.max(bestChargedScore, moveScore);
            }
        });
        
        offensiveScore = bestFastScore + bestChargedScore;
        
        // Calculate defensive score (opponent's moves vs your pokemon)
        let defensiveScore = 0;
        if (currentOpponent && currentOpponent.pvp_moves) {
            let opponentBestFastScore = -Infinity;
            let opponentBestChargedScore = -Infinity;
            
            currentOpponent.pvp_moves.forEach(move => {
                // Calculate effectiveness of opponent's move against this pokemon
                const effectiveness = calculateMoveEffectiveness(move, pokemon.types);
                let moveScore = 0;
                
                if (effectiveness.label === 'Super Effective') {
                    moveScore = move.move_class === 'fast' ? -2 : -5; // Negative because it's bad for us
                } else if (effectiveness.label === 'Not Very Effective') {
                    moveScore = move.move_class === 'fast' ? 1 : 3; // Positive because it's good for us
                } else if (effectiveness.label === 'Immune') {
                    moveScore = move.move_class === 'fast' ? 2 : 5; // Positive because it's good for us
                }
                // Neutral = 0
                
                if (move.move_class === 'fast') {
                    opponentBestFastScore = Math.max(opponentBestFastScore, moveScore);
                } else {
                    opponentBestChargedScore = Math.max(opponentBestChargedScore, moveScore);
                }
            });
            
            defensiveScore = opponentBestFastScore + opponentBestChargedScore;
        }
        
        const totalScore = offensiveScore + defensiveScore;
        scores.push({
            pokemonName: pokemon.name,
            offensiveScore,
            defensiveScore,
            totalScore
        });
    });
    
    return scores;
}

function calculateMoveEffectiveness(move, defendingTypes) {
    // This is a simplified version - you might want to use the actual effectiveness calculation from your backend
    const effectiveness = currentOpponent.effectiveness.effectiveness[move.type] || 1;
    
    if (effectiveness > 1) {
        return { label: 'Super Effective' };
    } else if (effectiveness < 1 && effectiveness > 0) {
        return { label: 'Not Very Effective' };
    } else if (effectiveness === 0) {
        return { label: 'Immune' };
    } else {
        return { label: 'Neutral' };
    }
}

function renderOpponentMovesVsTeam(opponentMovesVsTeam, teamNames) {
    let html = '';
    if (!opponentMovesVsTeam || opponentMovesVsTeam.length === 0) {
        html = '<div class="no-data">No matchup data</div>';
    } else {
        html += `<table class="matchup-table"><thead><tr><th>Opponent Move</th>`;
        teamNames.forEach(name => {
            html += `<th>${name}</th>`;
        });
        html += `</tr></thead><tbody>`;
        opponentMovesVsTeam.forEach(row => {
            html += `<tr><td><span class="move-name">${row.move.name}</span> <span class="type-badge type-${row.move.type}">${row.move.type}</span> <span class="move-type">(${row.move.move_class})</span></td>`;
            row.vs_team.forEach(cell => {
                let effClass = '';
                if (cell.effectiveness.label === 'Super Effective') effClass = 'move-eff-super';
                else if (cell.effectiveness.label === 'Not Very Effective') effClass = 'move-eff-notvery';
                else if (cell.effectiveness.label === 'Immune') effClass = 'move-eff-immune';
                else effClass = 'move-eff-neutral';
                html += `<td><span class="move-effectiveness ${effClass}">${cell.effectiveness.label}</span></td>`;
            });
            html += `</tr>`;
        });
        html += `</tbody></table>`;
    }
    let matchupTable = document.getElementById('opponentMatchupTable');
    if (!matchupTable) {
        matchupTable = document.createElement('div');
        matchupTable.id = 'opponentMatchupTable';
        const info = document.getElementById('pokemonInfo');
        info.appendChild(matchupTable);
    }
    matchupTable.innerHTML = `<h3>Opponent's Moves vs Your Team</h3>` + html;
}

// Hook into selection changes
function onSelectionChange() {
    if (currentOpponent && userTeam.length > 0) {
        updateMatchupAnalysis();
    } else {
        // Clear effectiveness from team slots when no opponent
        userTeam.forEach(pokemon => {
            updateTeamSlot(pokemon.slot, pokemon, null, false);
        });
    }
}

// Initialize battle simulator functionality
function initBattleSimulator() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });

    // Pokémon selection
    document.getElementById('pokemon1Display').addEventListener('click', () => {
        openBattleModal('pokemon1');
    });

    document.getElementById('pokemon2Display').addEventListener('click', () => {
        openBattleModal('pokemon2');
    });

    // Battle modal
    document.getElementById('closeBattleModal').addEventListener('click', closeBattleModal);
    document.getElementById('battleModalSearch').addEventListener('input', handleBattleModalSearch);

    // Run battle button
    document.getElementById('runBattleBtn').addEventListener('click', runBattle);

    // Move selection changes
    ['pokemon1FastMove', 'pokemon1Charged1', 'pokemon1Charged2'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => updateBattleButton());
    });

    ['pokemon2FastMove', 'pokemon2Charged1', 'pokemon2Charged2'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => updateBattleButton());
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
}

function openBattleModal(forPokemon) {
    battleModalState.isOpen = true;
    battleModalState.selectingFor = forPokemon;
    document.getElementById('battleModal').classList.remove('hidden');
    document.getElementById('battleModalSearch').value = '';
    document.getElementById('battleModalResults').innerHTML = '';
    document.getElementById('battleModalSearch').focus();
}

function closeBattleModal() {
    battleModalState.isOpen = false;
    battleModalState.selectingFor = null;
    document.getElementById('battleModal').classList.add('hidden');
}

async function handleBattleModalSearch(event) {
    const query = event.target.value.trim();
    if (query.length < 2) {
        document.getElementById('battleModalResults').innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`/api/search/${query}`);
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('battleModalResults').innerHTML = '<p class="error">No Pokemon found</p>';
            return;
        }

        displayBattleModalResults(data);
    } catch (error) {
        console.error('Error searching for Pokemon:', error);
        document.getElementById('battleModalResults').innerHTML = '<p class="error">Error searching for Pokemon</p>';
    }
}

function displayBattleModalResults(pokemonList) {
    const resultsContainer = document.getElementById('battleModalResults');
    resultsContainer.innerHTML = '';

    pokemonList.forEach(pokemon => {
        const pokemonElement = document.createElement('div');
        pokemonElement.className = 'modal-result-item';
        pokemonElement.innerHTML = `
            <img src="${pokemon.sprite}" alt="${pokemon.name}" class="result-sprite">
            <div class="result-info">
                <h4>${pokemon.name}</h4>
                <div class="types">
                    ${pokemon.types.map(type => `<span class="type-badge ${type}">${type}</span>`).join('')}
                </div>
            </div>
        `;
        
        pokemonElement.addEventListener('click', () => selectPokemonForBattle(pokemon));
        resultsContainer.appendChild(pokemonElement);
    });
}

async function selectPokemonForBattle(pokemon) {
    const forPokemon = battleModalState.selectingFor;
    
    try {
        // Get moves for the selected Pokémon
        const response = await fetch(`/api/pokemon/${pokemon.species_id}/moves`);
        const movesData = await response.json();
        
        if (movesData.error) {
            console.error('Error getting moves:', movesData.error);
            return;
        }

        // Update battle state
        battleState[forPokemon] = pokemon;
        battleState[`${forPokemon}Moves`] = movesData;

        // Update UI
        updatePokemonDisplay(forPokemon, pokemon, movesData);
        updateBattleButton();
        
        closeBattleModal();
    } catch (error) {
        console.error('Error selecting Pokemon for battle:', error);
    }
}

function updatePokemonDisplay(forPokemon, pokemon, movesData) {
    const displayElement = document.getElementById(`${forPokemon}Display`);
    const movesElement = document.getElementById(`${forPokemon}Moves`);
    
    // Update Pokémon display
    displayElement.innerHTML = `
        <div class="pokemon-selected">
            <img src="${pokemon.sprite}" alt="${pokemon.name}">
            <div class="pokemon-selected-info">
                <h5>${pokemon.name}</h5>
                <div class="types">
                    ${pokemon.types.map(type => `<span class="type-badge ${type}">${type}</span>`).join('')}
                </div>
            </div>
        </div>
    `;
    
    // Show moves selection
    movesElement.style.display = 'block';
    
    // Populate move dropdowns
    populateMoveDropdowns(forPokemon, movesData);
}

function populateMoveDropdowns(forPokemon, movesData) {
    // Fast moves
    const fastSelect = document.getElementById(`${forPokemon}FastMove`);
    fastSelect.innerHTML = '<option value="">Select Fast Move</option>';
    movesData.fast_moves.forEach(move => {
        const option = document.createElement('option');
        option.value = move.id;
        option.textContent = `${move.name} (${move.power} power, ${move.energyGain} energy)`;
        if (movesData.best_moveset && movesData.best_moveset.fast === move.id) {
            option.textContent += ' ★';
        }
        fastSelect.appendChild(option);
    });

    // Charged moves
    const charged1Select = document.getElementById(`${forPokemon}Charged1`);
    const charged2Select = document.getElementById(`${forPokemon}Charged2`);
    
    charged1Select.innerHTML = '<option value="">Select Charged Move 1</option>';
    charged2Select.innerHTML = '<option value="">Select Charged Move 2</option>';
    
    movesData.charged_moves.forEach(move => {
        const option1 = document.createElement('option');
        const option2 = document.createElement('option');
        
        option1.value = move.id;
        option2.value = move.id;
        
        const moveText = `${move.name} (${move.power} power, ${move.energy} energy)`;
        option1.textContent = moveText;
        option2.textContent = moveText;
        
        if (movesData.best_moveset) {
            if (movesData.best_moveset.charged1 === move.id) {
                option1.textContent += ' ★';
            }
            if (movesData.best_moveset.charged2 === move.id) {
                option2.textContent += ' ★';
            }
        }
        
        charged1Select.appendChild(option1.cloneNode(true));
        charged2Select.appendChild(option2.cloneNode(true));
    });

    // Set best moves if available
    if (movesData.best_moveset) {
        if (movesData.best_moveset.fast) {
            fastSelect.value = movesData.best_moveset.fast;
        }
        if (movesData.best_moveset.charged1) {
            charged1Select.value = movesData.best_moveset.charged1;
        }
        if (movesData.best_moveset.charged2) {
            charged2Select.value = movesData.best_moveset.charged2;
        }
    }
}

function updateBattleButton() {
    const runButton = document.getElementById('runBattleBtn');
    const canRun = battleState.pokemon1 && battleState.pokemon2 && 
                   document.getElementById('pokemon1FastMove').value &&
                   document.getElementById('pokemon2FastMove').value;
    
    runButton.disabled = !canRun;
}

async function runBattle() {
    const runButton = document.getElementById('runBattleBtn');
    runButton.disabled = true;
    runButton.textContent = 'Running Battle...';

    try {
        // Collect battle data
        const battleData = {
            p1_id: battleState.pokemon1.species_id,
            p2_id: battleState.pokemon2.species_id,
            p1_moves: {
                fast: document.getElementById('pokemon1FastMove').value,
                charged1: document.getElementById('pokemon1Charged1').value,
                charged2: document.getElementById('pokemon1Charged2').value
            },
            p2_moves: {
                fast: document.getElementById('pokemon2FastMove').value,
                charged1: document.getElementById('pokemon2Charged1').value,
                charged2: document.getElementById('pokemon2Charged2').value
            },
            p1_shields: parseInt(document.getElementById('pokemon1Shields').value),
            p2_shields: parseInt(document.getElementById('pokemon2Shields').value)
        };

        // Remove empty charged moves
        if (!battleData.p1_moves.charged1) delete battleData.p1_moves.charged1;
        if (!battleData.p1_moves.charged2) delete battleData.p1_moves.charged2;
        if (!battleData.p2_moves.charged1) delete battleData.p2_moves.charged1;
        if (!battleData.p2_moves.charged2) delete battleData.p2_moves.charged2;

        const response = await fetch('/api/battle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(battleData)
        });

        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }

        displayBattleResults(result);
    } catch (error) {
        console.error('Battle simulation failed:', error);
        alert('Battle simulation failed: ' + error.message);
    } finally {
        runButton.disabled = false;
        runButton.textContent = 'Run Battle';
    }
}

function displayBattleResults(result) {
    const resultsElement = document.getElementById('battleResults');
    resultsElement.classList.remove('hidden');

    // Update winner display
    const winnerName = result.winner === 'tie' ? 'Tie' : 
                      result.winner === battleState.pokemon1.species_id ? battleState.pokemon1.name :
                      battleState.pokemon2.name;
    document.getElementById('winnerName').textContent = winnerName;

    // Update battle stats
    document.getElementById('battleTurns').textContent = result.turns;
    document.getElementById('battleRating').textContent = Math.round(result.battle_rating * 100) + '%';

    // Update final HP
    document.getElementById('pokemon1FinalHP').textContent = result.p1_final_hp;
    document.getElementById('pokemon2FinalHP').textContent = result.p2_final_hp;

    // Display timeline
    displayBattleTimeline(result.timeline);
}

function displayBattleTimeline(timeline) {
    const container = document.getElementById('timelineContainer');
    container.innerHTML = '';

    timeline.forEach(entry => {
        const entryElement = document.createElement('div');
        entryElement.className = `timeline-entry ${entry.type}-move`;
        
        let actionText = '';
        let detailsText = '';

        if (entry.type === 'fast') {
            actionText = `${entry.attacker} uses ${entry.move}`;
            detailsText = `Damage: ${entry.damage} | Energy gained: ${entry.energy_gained} | ${entry.defender} HP: ${entry.defender_hp_remaining}`;
        } else if (entry.type === 'charged') {
            actionText = `${entry.attacker} uses ${entry.move}`;
            if (entry.shield_used) {
                detailsText = `SHIELDED | Energy used: ${entry.energy_used} | ${entry.defender} HP: ${entry.defender_hp_remaining}`;
            } else {
                detailsText = `Damage: ${entry.damage} | Energy used: ${entry.energy_used} | ${entry.defender} HP: ${entry.defender_hp_remaining}`;
            }
        }

        if (entry.buff_applied) {
            detailsText += ' | Buff applied';
        }

        entryElement.innerHTML = `
            <span class="timeline-turn">T${entry.turn}</span>
            <span class="timeline-action">${actionText}</span>
            <span class="timeline-details">${detailsText}</span>
        `;

        container.appendChild(entryElement);
    });
}

// Initialize battle simulator when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // ... existing initialization code ...
    
    initBattleSimulator();
}); 