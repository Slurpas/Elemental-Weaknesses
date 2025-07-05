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

// Battle Simulation State
let battleSimulationState = {
    shieldCount: 2,
    simulations: {} // Cache for battle results
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

// Tab switching - moved to initBattleSimulator to avoid conflicts

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
    displayMoves(pokemon.pvp_moves, pokemon.types, true); // true = isOpponent
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

function calculateEffectiveDPE(move, opponent, pokemonTypes = []) {
    console.log('calculateEffectiveDPE called with:', { move, opponent: opponent.name, pokemonTypes });
    if (!move.power || !move.energy || move.energy === 0) {
        console.log('Missing power/energy, returning base DPE:', move.dpe);
        return move.dpe;
    }
    
    // Get base power and energy from move data
    const basePower = move.power;
    const energy = move.energy;
    
    // Apply STAB if move type matches Pokémon type
    const stabMultiplier = pokemonTypes.includes(move.type) ? 1.2 : 1.0;
    
    // Get type effectiveness against the opponent
    let typeMultiplier = 1.0;
    if (move.type && opponent.types) {
        // Calculate effectiveness of this move type against opponent types
        const effectiveness = calculateMoveEffectiveness(move, opponent.types);
        typeMultiplier = effectiveness.multiplier;
    }
    
    // Calculate effective damage
    const effectiveDamage = basePower * stabMultiplier * typeMultiplier;
    const effectiveDPE = effectiveDamage / energy;
    
    return effectiveDPE.toFixed(2);
}

function displayMoves(pvpMoves, pokemonTypes = [], isOpponent = false) {
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
                else effClass = 'move-eff-neutral';
            }
            // Calculate effective DPE if we have opponent data (only for team Pokémon, not opponent)
            let effectiveDpeDisplay = '';
            if (!isOpponent && move.dpe && move.move_class === 'charged' && currentOpponent) {
                const baseDpe = parseFloat(move.dpe);
                const effectiveDpe = parseFloat(calculateEffectiveDPE(move, currentOpponent, pokemonTypes));
                if (effectiveDpe !== baseDpe) {
                    const modifier = effectiveDpe - baseDpe;
                    const modifierSign = modifier > 0 ? '+' : '';
                    effectiveDpeDisplay = `<span class="move-effective-dpe">(${effectiveDpe.toFixed(2)} ${modifierSign}${modifier.toFixed(2)} vs ${currentOpponent.name})</span>`;
                }
            }
            
            return `
            <div class="move-item">
                <div class="move-info">
                    <span class="move-name">${move.name}</span>
                    <span class="type-badge type-${move.type}">${move.type}</span>
                    <span class="move-type">(${move.move_class === 'fast' ? 'Fast Move' : 'Charged Move'})</span>
                    ${!isOpponent && move.dpe ? `<span class="move-dpe">DPE: ${move.dpe}${effectiveDpeDisplay}</span>` : ''}
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

// Move selector functionality
let currentMoveSelector = null;

window.openMoveSelector = function(slotNumber, currentMoveName, moveClass) {
    currentMoveSelector = { slotNumber, currentMoveName, moveClass, currentMoveName };
    
    // Get the Pokémon in this slot
    const pokemon = userTeam.find(p => p.slot === slotNumber);
    if (!pokemon) return;
    
    // Get all available moves for this Pokémon
    fetch(`/api/pokemon/${pokemon.name}/moves`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert('Failed to load moves');
                return;
            }
            
            const moves = moveClass === 'fast' ? data.fast_moves : data.charged_moves;
            showMoveSelector(moves, currentMoveName, moveClass);
        })
        .catch(error => {
            console.error('Error loading moves:', error);
            alert('Failed to load moves');
        });
};

function showMoveSelector(moves, currentMoveName, moveClass) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('moveSelectorModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'moveSelectorModal';
        modal.className = 'modal hidden';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Select ${moveClass === 'fast' ? 'Fast' : 'Charged'} Move</h3>
                    <button class="close-btn" onclick="closeMoveSelector()">×</button>
                </div>
                <div class="modal-body">
                    <div id="moveSelectorList"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeMoveSelector();
        });
    }
    
    // Populate moves list
    const movesList = document.getElementById('moveSelectorList');
    movesList.innerHTML = moves.map(move => `
        <div class="move-selector-item ${move.name === currentMoveName ? 'selected' : ''}" 
             onclick="selectMove('${move.name}')">
            <div class="move-selector-name">${move.name}</div>
            <div class="move-selector-details">
                <span class="type-badge type-${move.type}">${move.type}</span>
                ${move.power ? `<span class="move-power">${move.power} power</span>` : ''}
                ${move.energy ? `<span class="move-energy">${move.energy} energy</span>` : ''}
                ${move.energyGain ? `<span class="move-energy-gain">+${move.energyGain} energy</span>` : ''}
            </div>
        </div>
    `).join('');
    
    // Show modal
    modal.classList.remove('hidden');
}

window.selectMove = function(moveName) {
    if (!currentMoveSelector) return;
    
    const { slotNumber, moveClass } = currentMoveSelector;
    const pokemon = userTeam.find(p => p.slot === slotNumber);
    
    if (!pokemon) return;
    
    // Get the move details from the API to update the pvp_moves array
    fetch(`/api/pokemon/${pokemon.name}/moves`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert('Failed to load move details');
                return;
            }
            
            // Find the selected move in the API response
            const allMoves = [...(data.fast_moves || []), ...(data.charged_moves || [])];
            const selectedMove = allMoves.find(m => m.name === moveName);
            
            if (!selectedMove) {
                alert('Move not found');
                return;
            }
            
            console.log('Selected move before processing:', selectedMove);
            
            // Ensure the selected move has all necessary properties for DPE calculation
            if (selectedMove.move_class === 'charged' || moveClass === 'charged') {
                // Set move_class if not present
                selectedMove.move_class = 'charged';
                
                // Ensure power and energy are available for effective DPE calculation
                if (!selectedMove.power && selectedMove.power !== 0) {
                    selectedMove.power = 0; // Default if not provided
                }
                if (!selectedMove.energy && selectedMove.energy !== 0) {
                    selectedMove.energy = 1; // Default if not provided
                }
                
                // Calculate DPE if not provided
                if (!selectedMove.dpe) {
                    selectedMove.dpe = (selectedMove.power / selectedMove.energy).toFixed(2);
                }
            } else {
                // Set move_class for fast moves
                selectedMove.move_class = 'fast';
            }
            
            console.log('Selected move after processing:', selectedMove);
            
            // Update the pvp_moves array - replace the specific move that was clicked
            const currentMoveName = currentMoveSelector.currentMoveName;
            const moveIndex = pokemon.pvp_moves.findIndex(m => m.name === currentMoveName);
            
            if (moveIndex !== -1) {
                // Replace the specific move that was clicked
                pokemon.pvp_moves[moveIndex] = selectedMove;
            } else {
                // If not found, add it to the appropriate position
                if (moveClass === 'fast') {
                    pokemon.pvp_moves.unshift(selectedMove);
                } else {
                    pokemon.pvp_moves.push(selectedMove);
                }
            }
            
            // Update the UI
            updateTeamSlot(slotNumber, pokemon);
            closeMoveSelector();
            
            // Force refresh of all team slots to update DPE displays
            refreshTeamMovesDisplay();
            
            // Re-run battle simulations
            onSelectionChange();
        })
        .catch(error => {
            console.error('Error updating move:', error);
            alert('Failed to update move');
        });
};

window.closeMoveSelector = function() {
    const modal = document.getElementById('moveSelectorModal');
    if (modal) {
        modal.classList.add('hidden');
    }
    currentMoveSelector = null;
};

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
            speciesId: data.speciesId || data.name.toLowerCase().replace(' ', '_'),
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
                        else effClass = 'move-eff-neutral';
                                effectivenessHTML = `<span class="move-effectiveness ${effClass}">${moveEffectiveness.effectiveness.label}</span>`;
                            }
                        }
                        
                        // Calculate effective DPE for team moves
                        let effectiveDpeDisplay = '';
                        let moveRankingClass = '';
                        let rankingBadge = '';
                        
                        if (move.dpe && move.move_class === 'charged') {
                            const baseDpe = parseFloat(move.dpe);
                            if (currentOpponent) {
                                const effectiveDpe = parseFloat(calculateEffectiveDPE(move, currentOpponent, pokemon.types));
                                if (effectiveDpe !== baseDpe) {
                                    const modifier = effectiveDpe - baseDpe;
                                    const modifierSign = modifier > 0 ? '+' : '';
                                    
                                    // Calculate type effectiveness multiplier
                                    const effectivenessMultiplier = effectiveDpe / baseDpe;
                                    let effectivenessClass = '';
                                    
                                    if (effectivenessMultiplier >= 2.0) {
                                        effectivenessClass = 'dpe-super-effective'; // Bold green for 2x+
                                    } else if (effectivenessMultiplier >= 1.5) {
                                        effectivenessClass = 'dpe-effective'; // Green for 1.5x+
                                    } else if (effectivenessMultiplier <= 0.25) {
                                        effectivenessClass = 'dpe-double-resisted'; // Super red for 0.25x
                                    } else if (effectivenessMultiplier < 1.0) {
                                        effectivenessClass = 'dpe-resisted'; // Fairly red for <1x
                                    } else {
                                        effectivenessClass = 'dpe-neutral'; // Normal for 1x
                                    }
                                    
                                    effectiveDpeDisplay = `<span class="move-effective-dpe ${effectivenessClass}">(${baseDpe.toFixed(2)} ${modifierSign}${modifier.toFixed(2)} vs ${currentOpponent.name})</span>`;
                                }
                            }
                        }
                        
                        // Calculate move ranking for charged moves
                        if (move.move_class === 'charged' && currentOpponent && pokemon.pvp_moves) {
                            const chargedMoves = pokemon.pvp_moves.filter(m => m.move_class === 'charged' && m.dpe);
                            if (chargedMoves.length > 1) {
                                // Calculate effective DPE for all charged moves
                                const moveRankings = chargedMoves.map(m => {
                                    const baseDpe = parseFloat(m.dpe);
                                    const effectiveDpe = parseFloat(calculateEffectiveDPE(m, currentOpponent, pokemon.types));
                                    return { move: m, effectiveDpe, baseDpe };
                                }).sort((a, b) => b.effectiveDpe - a.effectiveDpe);
                                
                                // Find this move's rank
                                const currentMoveRank = moveRankings.findIndex(r => r.move.name === move.name);
                                const bestMove = moveRankings[0];
                                const currentMove = moveRankings[currentMoveRank];
                                
                                if (currentMoveRank >= 0) {
                                    // Calculate percentage difference from best
                                    const percentageDiff = ((currentMove.effectiveDpe - bestMove.effectiveDpe) / bestMove.effectiveDpe) * 100;
                                    
                                    // Assign ranking class and badge based on percentage difference
                                    if (currentMoveRank === 0) {
                                        moveRankingClass = 'move-best';
                                        rankingBadge = '<span class="ranking-badge ranking-gold">🥇</span>';
                                    } else if (percentageDiff >= -10) {
                                        // Within 10% of best - excellent
                                        moveRankingClass = 'move-excellent';
                                        rankingBadge = '<span class="ranking-badge ranking-silver">🥈</span>';
                                    } else if (percentageDiff >= -25) {
                                        // Within 25% of best - good
                                        moveRankingClass = 'move-good';
                                        rankingBadge = '<span class="ranking-badge ranking-bronze">🥉</span>';
                                    } else if (percentageDiff >= -50) {
                                        // Within 50% of best - mediocre
                                        moveRankingClass = 'move-mediocre';
                                        rankingBadge = '<span class="ranking-badge ranking-mediocre">⚠️</span>';
                                    } else {
                                        // More than 50% worse than best - poor
                                        moveRankingClass = 'move-poor';
                                        rankingBadge = '<span class="ranking-badge ranking-poor">❌</span>';
                                    }
                                    
                                    // Add percentage indicator for non-best moves
                                    if (currentMoveRank > 0) {
                                        rankingBadge += `<span class="ranking-percentage">${percentageDiff.toFixed(1)}%</span>`;
                                    }
                                }
                            }
                        }
                        
                        return `
                            <div class="move-item ${moveRankingClass}" onclick="event.stopPropagation(); openMoveSelector('${slotNumber}', '${move.name}', '${move.move_class}')">
                                <div class="move-info">
                                    <div class="move-name">${rankingBadge}${move.name}</div>
                                    <div class="move-details">
                                        <span class="type-badge type-${move.type}">${move.type}</span>
                                        <span class="move-type">(${move.move_class === 'fast' ? 'Fast Move' : 'Charged Move'})</span>
                                        ${move.dpe ? `<span class="move-dpe">DPE: ${currentOpponent && move.move_class === 'charged' ? parseFloat(calculateEffectiveDPE(move, currentOpponent, pokemon.types)).toFixed(2) : move.dpe}${effectiveDpeDisplay}</span>` : (move.move_class === 'charged' && move.power && move.energy) ? `<span class="move-dpe">DPE: ${currentOpponent ? parseFloat(calculateEffectiveDPE(move, currentOpponent, pokemon.types)).toFixed(2) : (move.power / move.energy).toFixed(2)}${effectiveDpeDisplay}</span>` : ''}
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

    // Generate battle result HTML if opponent is selected
    let battleResultHTML = '';
    if (currentOpponent) {
        // Find battle result for this team member
        const battleResult = window.currentBattleResults ? 
            window.currentBattleResults.find(result => result.teamPokemon.name === pokemon.name) : null;
        
        if (battleResult) {
            const winner = battleResult.battleResult.winner;
            const battleRating = battleResult.battleResult.battle_rating;
            const teamHpRemaining = battleResult.battleResult.p1_final_hp;
            const opponentHpRemaining = battleResult.battleResult.p2_final_hp;
            
            // Determine what to display based on winner and HP
            let ratingDisplay, winnerText, winnerClass, ratingColor;
            
            // Check if it's actually a tie (both Pokémon have 0 HP)
            const isActualTie = teamHpRemaining === 0 && opponentHpRemaining === 0;
            
            if (isActualTie) {
                // True tie - both fainted
                ratingDisplay = 'Tie';
                winnerText = 'Tie';
                winnerClass = 'tie';
                ratingColor = 'neutral';
            } else if (teamHpRemaining > 0 && opponentHpRemaining === 0) {
                // Your Pokémon won - opponent fainted
                const maxHp = battleResult.battleResult.p1_max_hp || pokemon.stats?.hp || 100;
                const hpPercent = Math.round((teamHpRemaining / maxHp) * 100);
                ratingDisplay = `${hpPercent}% HP`;
                winnerText = 'Wins';
                winnerClass = 'wins';
                ratingColor = hpPercent > 50 ? 'excellent' : hpPercent > 25 ? 'good' : 'close';
            } else if (opponentHpRemaining > 0 && teamHpRemaining === 0) {
                // Opponent won - your Pokémon fainted
                const maxHp = battleResult.battleResult.p2_max_hp || currentOpponent.stats?.hp || 100;
                const hpPercent = Math.round((opponentHpRemaining / maxHp) * 100);
                ratingDisplay = `${hpPercent}% HP`;
                winnerText = 'Loses';
                winnerClass = 'loses';
                ratingColor = hpPercent > 50 ? 'bad' : hpPercent > 25 ? 'close-loss' : 'close';
            } else if (teamHpRemaining > opponentHpRemaining) {
                // Your Pokémon won with more HP remaining
                const maxHp = battleResult.battleResult.p1_max_hp || pokemon.stats?.hp || 100;
                const hpPercent = Math.round((teamHpRemaining / maxHp) * 100);
                ratingDisplay = `${hpPercent}% HP`;
                winnerText = 'Wins';
                winnerClass = 'wins';
                ratingColor = hpPercent > 50 ? 'excellent' : hpPercent > 25 ? 'good' : 'close';
            } else if (opponentHpRemaining > teamHpRemaining) {
                // Opponent won with more HP remaining
                const maxHp = battleResult.battleResult.p2_max_hp || currentOpponent.stats?.hp || 100;
                const hpPercent = Math.round((opponentHpRemaining / maxHp) * 100);
                ratingDisplay = `${hpPercent}% HP`;
                winnerText = 'Loses';
                winnerClass = 'loses';
                ratingColor = hpPercent > 50 ? 'bad' : hpPercent > 25 ? 'close-loss' : 'close';
            } else {
                // Equal HP remaining (very rare)
                const maxHp = battleResult.battleResult.p1_max_hp || pokemon.stats?.hp || 100;
                const hpPercent = Math.round((teamHpRemaining / maxHp) * 100);
                ratingDisplay = `${hpPercent}% HP`;
                winnerText = 'Tie';
                winnerClass = 'tie';
                ratingColor = 'neutral';
            }

            battleResultHTML = `
                <div class="team-battle-result">
                    <h4>vs ${currentOpponent.name}</h4>
                    <div class="battle-result-display">
                        <div class="rating-value rating-${ratingColor}">${ratingDisplay}</div>
                        <div class="winner-indicator ${winnerClass}">${winnerText}</div>
                        <div class="hp-details">You: ${teamHpRemaining} HP | Opponent: ${opponentHpRemaining} HP</div>
                    </div>
                </div>
            `;
        } else {
            battleResultHTML = `
                <div class="team-battle-result">
                    <h4>vs ${currentOpponent.name}</h4>
                    <div class="battle-result-display">
                        <div class="no-battle-data">No battle data</div>
                    </div>
                </div>
            `;
        }
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
                    ${battleResultHTML}
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
    
    // Run battle simulations if there's a current opponent
    if (currentOpponent) {
        runBattleSimulations();
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



// Close search results when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-section')) {
        searchResults.style.display = 'none';
    }
});

// Add some CSS for the no-data class and move selector
const style = document.createElement('style');
style.textContent = `
    .no-data {
        color: #999;
        font-style: italic;
        padding: 10px;
    }
    
    .move-selector-item {
        padding: 10px;
        border: 1px solid #ddd;
        margin: 5px 0;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .move-selector-item:hover {
        background-color: #f5f5f5;
    }
    
    .move-selector-item.selected {
        background-color: #e3f2fd;
        border-color: #2196f3;
    }
    
    .move-selector-name {
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .move-selector-details {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        font-size: 0.9em;
        color: #666;
    }
    
    .move-item {
        cursor: pointer;
        transition: background-color 0.2s;
        border-radius: 3px;
        padding: 2px;
    }
    
    .move-item:hover {
        background-color: #f0f0f0;
    }
    
    .matchup-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 0.9em;
    }
    
    .matchup-table th,
    .matchup-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
    }
    
    .matchup-table th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    
    .matchup-table td:first-child {
        text-align: left;
        font-weight: bold;
    }
    
    #opponentMatchupTable {
        margin-top: 20px;
        padding: 15px;
        background-color: #f9f9f9;
        border-radius: 5px;
    }
    
    #opponentMatchupTable h3 {
        margin-top: 0;
        margin-bottom: 15px;
        color: #333;
    }
    
    /* DPE Effectiveness Color Coding */
    .move-effective-dpe.dpe-super-effective {
        color: #00aa00;
        font-weight: bold;
        background-color: #e8f5e8;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    .move-effective-dpe.dpe-effective {
        color: #008800;
        font-weight: bold;
        background-color: #f0f8f0;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    .move-effective-dpe.dpe-neutral {
        color: #666;
        background-color: #f5f5f5;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    .move-effective-dpe.dpe-resisted {
        color: #cc0000;
        background-color: #ffe8e8;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    .move-effective-dpe.dpe-double-resisted {
        color: #990000;
        font-weight: bold;
        background-color: #ffcccc;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Move Ranking System - Color Scale */
    .move-item.move-best {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border: 2px solid #28a745;
    }
    
    .move-item.move-excellent {
        background-color: #e8f5e8;
        border-left: 4px solid #00aa00;
        border: 1px solid #00aa00;
    }
    
    .move-item.move-good {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border: 1px solid #ffc107;
    }
    
    .move-item.move-mediocre {
        background-color: #ffeaa7;
        border-left: 4px solid #f39c12;
        border: 1px solid #f39c12;
    }
    
    .move-item.move-poor {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border: 1px solid #dc3545;
    }
    
    .ranking-badge {
        margin-right: 8px;
        font-size: 1.2em;
    }
    
    .ranking-badge.ranking-gold {
        color: #ffd700;
    }
    
    .ranking-badge.ranking-silver {
        color: #c0c0c0;
    }
    
    .ranking-badge.ranking-bronze {
        color: #cd7f32;
    }
    
    .ranking-badge.ranking-mediocre {
        color: #f39c12;
    }
    
    .ranking-badge.ranking-poor {
        color: #dc3545;
    }
    
    .ranking-percentage {
        font-size: 0.8em;
        color: #666;
        margin-left: 4px;
        font-weight: bold;
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
    // Calculate type effectiveness of move.type against defendingTypes
    let multiplier = 1.0;
    
    // Type effectiveness chart (simplified)
    const effectivenessChart = {
        'normal': { 'rock': 0.5, 'ghost': 0, 'steel': 0.5 },
        'fire': { 'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'steel': 2 },
        'water': { 'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5 },
        'electric': { 'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5 },
        'grass': { 'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2, 'dragon': 0.5, 'steel': 0.5 },
        'ice': { 'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5 },
        'fighting': { 'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0, 'steel': 2, 'fairy': 0.5 },
        'poison': { 'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0, 'fairy': 2 },
        'ground': { 'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2 },
        'flying': { 'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2, 'rock': 0.5, 'steel': 0.5 },
        'psychic': { 'fighting': 2, 'poison': 2, 'psychic': 0.5, 'dark': 0, 'steel': 0.5 },
        'bug': { 'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'dark': 2, 'steel': 0.5, 'fairy': 0.5 },
        'rock': { 'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5 },
        'ghost': { 'normal': 0, 'psychic': 2, 'ghost': 2, 'dark': 0.5 },
        'dragon': { 'dragon': 2, 'steel': 0.5, 'fairy': 0 },
        'dark': { 'fighting': 0.5, 'psychic': 2, 'ghost': 2, 'dark': 0.5, 'fairy': 0.5 },
        'steel': { 'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5, 'fairy': 2 },
        'fairy': { 'fighting': 2, 'poison': 0.5, 'dragon': 2, 'dark': 2, 'steel': 0.5 }
    };
    
    // Calculate effectiveness against each defending type
    defendingTypes.forEach(defendingType => {
        if (effectivenessChart[move.type] && effectivenessChart[move.type][defendingType]) {
            multiplier *= effectivenessChart[move.type][defendingType];
        }
    });
    
    if (multiplier > 1) {
        return { label: 'Super Effective', multiplier: multiplier };
    } else if (multiplier < 1 && multiplier > 0) {
        return { label: 'Not Very Effective', multiplier: multiplier };
    } else {
        return { label: 'Neutral', multiplier: 1.0 };
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
function refreshTeamMovesDisplay() {
    // Refresh moves display for all team Pokémon to update effective DPE
    userTeam.forEach(pokemon => {
        // Force a complete refresh of the team slot to recalculate DPE
        updateTeamSlot(pokemon.slot, pokemon, null, false);
    });
}

function onSelectionChange() {
    if (currentOpponent && userTeam.length > 0) {
        runBattleSimulations();
        refreshTeamMovesDisplay();
        updateMatchupAnalysis(); // Add matchup analysis
    } else {
        // Clear effectiveness from team slots when no opponent
        userTeam.forEach(pokemon => {
            updateTeamSlot(pokemon.slot, pokemon, null, false);
        });
        // Clear battle results
        window.currentBattleResults = null;
        
        // Clear matchup table
        const matchupTable = document.getElementById('opponentMatchupTable');
        if (matchupTable) {
            matchupTable.innerHTML = '';
        }
        
        // Refresh team moves display to show base DPE without opponent
        refreshTeamMovesDisplay();
    }
}

// Initialize battle simulator functionality
function initBattleSimulations() {
    // Shield slider
    const shieldSlider = document.getElementById('shieldSlider');
    const shieldValue = document.getElementById('shieldValue');
    
    shieldSlider.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        battleSimulationState.shieldCount = value;
        shieldValue.textContent = value;
        
        // Clear cache and re-run simulations if opponent is selected
        if (currentOpponent) {
            battleSimulationState.simulations = {};
            runBattleSimulations();
        }
    });
}

async function runBattleSimulations() {
    if (!currentOpponent || userTeam.length === 0) {
        console.log('No opponent or team members, skipping battle simulations');
        return;
    }

    console.log('Starting battle simulations...');
    console.log('Current opponent:', currentOpponent);
    console.log('User team:', userTeam);

    const results = [];
    const shieldCount = battleSimulationState.shieldCount;

    // Run simulations for each team member vs opponent
    for (let i = 0; i < userTeam.length; i++) {
        const teamPokemon = userTeam[i];
        if (!teamPokemon) continue;

        console.log(`Simulating battle for ${teamPokemon.name} vs ${currentOpponent.name}`);

        try {
            // Get PvP moves for team Pokémon
            const teamMoves = await getPvPMovesForPokemon(teamPokemon.name);
            console.log(`Team moves for ${teamPokemon.name}:`, teamMoves);
            if (!teamMoves || teamMoves.length === 0) {
                console.log(`No PvP moves found for ${teamPokemon.name}`);
                continue;
            }

            // Get PvP moves for opponent
            const opponentMoves = await getPvPMovesForPokemon(currentOpponent.name);
            console.log(`Opponent moves for ${currentOpponent.name}:`, opponentMoves);
            if (!opponentMoves || opponentMoves.length === 0) {
                console.log(`No PvP moves found for ${currentOpponent.name}`);
                continue;
            }

            // Run battle simulation
            const battleResult = await runSingleBattle(
                teamPokemon, teamMoves,
                currentOpponent, opponentMoves,
                shieldCount
            );

            console.log(`Battle result for ${teamPokemon.name}:`, battleResult);

            results.push({
                teamPokemon,
                battleResult,
                slotIndex: i
            });

        } catch (error) {
            console.error(`Error simulating battle for ${teamPokemon.name}:`, error);
        }
    }

    console.log('All battle results:', results);

    // Sort by battle rating (highest first)
    results.sort((a, b) => b.battleResult.battle_rating - a.battleResult.battle_rating);

    // Display results
    displayBattleSimulations(results);
}

async function getPvPMovesForPokemon(pokemonName) {
    try {
        console.log(`Getting PvP moves for: ${pokemonName}`);
        
        // Try with the name as-is first
        let response = await fetch(`/api/pokemon/${pokemonName}`);
        let data = await response.json();
        
        console.log(`Initial response for ${pokemonName}:`, data);
        
        // If not found and it's an alternate form, try with speciesId format
        if (data.error && pokemonName.includes('(')) {
            const speciesId = pokemonName.toLowerCase()
                .replace('(', '')
                .replace(')', '')
                .replace(' ', '_')
                .replace('galarian', 'galar')
                .replace('alolan', 'alola')
                .replace('hisuian', 'hisui');
            
            console.log(`Trying with speciesId: ${speciesId}`);
            response = await fetch(`/api/pokemon/${speciesId}`);
            data = await response.json();
            console.log(`SpeciesId response for ${pokemonName}:`, data);
        }
        
        const pvpMoves = data.pvp_moves || [];
        console.log(`PvP moves for ${pokemonName}:`, pvpMoves);
        return pvpMoves;
    } catch (error) {
        console.error(`Error getting PvP moves for ${pokemonName}:`, error);
        return [];
    }
}

async function runSingleBattle(teamPokemon, teamMoves, opponentPokemon, opponentMoves, shieldCount) {
    console.log('Running single battle with:', { teamPokemon, teamMoves, opponentPokemon, opponentMoves, shieldCount });
    
    // Prepare battle data using best PvP moves
    const teamFastMove = teamMoves.find(m => m.move_class === 'fast');
    const teamChargedMoves = teamMoves.filter(m => m.move_class === 'charged').slice(0, 2);
    
    const opponentFastMove = opponentMoves.find(m => m.move_class === 'fast');
    const opponentChargedMoves = opponentMoves.filter(m => m.move_class === 'charged').slice(0, 2);

    console.log('Selected moves:', {
        teamFastMove,
        teamChargedMoves,
        opponentFastMove,
        opponentChargedMoves
    });

    // Use speciesId for API calls (handles alternate forms correctly)
    let teamId = teamPokemon.speciesId || teamPokemon.name;
    let opponentId = opponentPokemon.speciesId || opponentPokemon.name;
    
    // Handle alternate forms by converting names to speciesId format
    if (teamPokemon.name.includes('(') && !teamId.includes('_')) {
        teamId = teamPokemon.name.toLowerCase()
            .replace('(', '')
            .replace(')', '')
            .replace(' ', '_')
            .replace('galarian', 'galarian')  // Keep as 'galarian', not 'galar'
            .replace('alolan', 'alolan')      // Keep as 'alolan', not 'alola'
            .replace('hisuian', 'hisuian');   // Keep as 'hisuian', not 'hisui'
    }
    
    if (opponentPokemon.name.includes('(') && !opponentId.includes('_')) {
        opponentId = opponentPokemon.name.toLowerCase()
            .replace('(', '')
            .replace(')', '')
            .replace(' ', '_')
            .replace('galarian', 'galarian')  // Keep as 'galarian', not 'galar'
            .replace('alolan', 'alolan')      // Keep as 'alolan', not 'alola'
            .replace('hisuian', 'hisuian');   // Keep as 'hisuian', not 'hisui'
    }

    console.log('Using IDs:', { teamId, opponentId });

    const battleData = {
        p1_id: teamId,
        p2_id: opponentId,
        p1_moves: {
            fast: teamFastMove ? teamFastMove.name.toUpperCase().replace(' ', '_') : null,
            charged1: teamChargedMoves[0] ? teamChargedMoves[0].name.toUpperCase().replace(' ', '_') : null,
            charged2: teamChargedMoves[1] ? teamChargedMoves[1].name.toUpperCase().replace(' ', '_') : null
        },
        p2_moves: {
            fast: opponentFastMove ? opponentFastMove.name.toUpperCase().replace(' ', '_') : null,
            charged1: opponentChargedMoves[0] ? opponentChargedMoves[0].name.toUpperCase().replace(' ', '_') : null,
            charged2: opponentChargedMoves[1] ? opponentChargedMoves[1].name.toUpperCase().replace(' ', '_') : null
        },
        p1_shields: shieldCount,
        p2_shields: shieldCount
    };

    console.log('Battle data before cleanup:', battleData);

    // Remove empty moves
    Object.keys(battleData.p1_moves).forEach(key => {
        if (!battleData.p1_moves[key]) delete battleData.p1_moves[key];
    });
    Object.keys(battleData.p2_moves).forEach(key => {
        if (!battleData.p2_moves[key]) delete battleData.p2_moves[key];
    });

    console.log('Final battle data:', battleData);

    try {
        const response = await fetch('/api/battle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(battleData)
        });

        const result = await response.json();
        console.log('Battle API response:', result);
        
        if (result.error) {
            throw new Error(result.error);
        }

        return result;
    } catch (error) {
        console.error('Battle simulation failed:', error);
        // Return a default result
        return {
            winner: 'tie',
            battle_rating: 0.5,
            p1_final_hp: 0,
            p2_final_hp: 0,
            turns: 0
        };
    }
}

function displayBattleSimulations(results) {
    // Store results globally for team slots to access
    window.currentBattleResults = results;
    
    // Update all team slots to show battle results
    userTeam.forEach(pokemon => {
        updateTeamSlot(pokemon.slot, pokemon);
    });

    // Find the best counter (highest rating)
    const bestRating = results.length > 0 ? results[0].battleResult.battle_rating : 0;

    // Update team slot borders to show best counter
    updateTeamSlotBorders(results, bestRating);
}

function updateTeamSlotBorders(results, bestRating) {
    // Clear all best-counter classes first
    document.querySelectorAll('.team-slot').forEach(slot => {
        slot.classList.remove('best-counter');
    });

    // Add best-counter class to slots with the best rating
    results.forEach(result => {
        if (result.battleResult.battle_rating === bestRating) {
            const slot = document.querySelector(`[data-slot="${result.slotIndex + 1}"]`);
            if (slot) {
                slot.classList.add('best-counter');
            }
        }
    });
}

// Initialize battle simulations when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // ... existing initialization code ...
    
    initBattleSimulations();
}); 