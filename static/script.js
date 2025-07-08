// DOM elements
const pokemonSearch = document.getElementById('pokemonSearch');
const searchBtn = document.getElementById('searchBtn');
const searchResults = document.getElementById('searchResults');
const pokemonInfo = document.getElementById('pokemonInfo');
const loading = document.getElementById('loading');
const error = document.getElementById('error');

// Help modal elements
const helpBtn = document.getElementById('helpBtn');
const helpModal = document.getElementById('helpModal');
const closeHelpModalBtn = document.getElementById('closeHelpModal');

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
    shieldAI: 'smart_30',
    cpCap: 1500,
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

// Help modal event listeners
helpBtn.addEventListener('click', showHelpModal);
closeHelpModalBtn.addEventListener('click', closeHelpModal);

// Close help modal when clicking outside
helpModal.addEventListener('click', (e) => {
    if (e.target === helpModal) {
        closeHelpModal();
    }
});

// Close help modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !helpModal.classList.contains('hidden')) {
        closeHelpModal();
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
                <img src="${pokemon.sprite}" alt="${pokemon.name}" style="width: 30px; height: 30px; margin-right: 10px;" onerror="console.error('Failed to load search sprite:', this.src)">
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
    // --- PATCH: Set default moves to PvPoke best moveset for opponent if available ---
    if (pokemon.pvpoke_moveset && pokemon.pvpoke_moveset.length > 0 && pokemon.pvp_moves && pokemon.pvp_moves.length > 0) {
        const bestFastMove = pokemon.pvp_moves.find(m => m.move_class === 'fast' && pokemon.pvpoke_moveset.includes(m.name.toUpperCase().replace(/ /g, '_')));
        const bestChargedMoves = pokemon.pvp_moves.filter(m => m.move_class === 'charged' && pokemon.pvpoke_moveset.includes(m.name.toUpperCase().replace(/ /g, '_')));
        let newPvpMoves = [];
        if (bestFastMove) newPvpMoves.push(bestFastMove);
        if (bestChargedMoves.length > 0) newPvpMoves = newPvpMoves.concat(bestChargedMoves);
        if (!bestFastMove) {
            const fallbackFast = pokemon.pvp_moves.find(m => m.move_class === 'fast');
            if (fallbackFast) newPvpMoves.unshift(fallbackFast);
        }
        while (newPvpMoves.filter(m => m.move_class === 'charged').length < 2) {
            const fallbackCharged = pokemon.pvp_moves.find(m => m.move_class === 'charged' && !newPvpMoves.includes(m));
            if (fallbackCharged) newPvpMoves.push(fallbackCharged);
            else break;
        }
        pokemon.pvp_moves = newPvpMoves;
    }
    // --- END PATCH ---
    currentOpponent = pokemon;
    console.log('Setting sprite for:', pokemon.name, 'URL:', pokemon.sprite);
    const spriteElement = document.getElementById('pokemonSprite');
    spriteElement.src = pokemon.sprite;
    spriteElement.onerror = () => console.error('Failed to load main sprite:', pokemon.sprite);
    spriteElement.onload = () => console.log('Successfully loaded main sprite:', pokemon.sprite);
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
    onSelectionChange().catch(error => {
        console.error('Error in onSelectionChange:', error);
    });
}

function displayEffectiveness(effectiveness) {
    // Debug log for effectiveness object
    console.log('[DEBUG] Opponent Effectiveness:', effectiveness);
    // Weaknesses
    let weaknessesHtml = '';
    if (effectiveness.weaknesses && effectiveness.weaknesses.length > 0) {
        effectiveness.weaknesses.forEach(([type, mult]) => {
            weaknessesHtml += `<span class="type-badge type-${type}" title="${mult}x">${type} (${mult}x)</span> `;
        });
    } else {
        weaknessesHtml = '<span class="none">None</span>';
    }
    // Resistances (single, double, triple)
    let resistancesHtml = '';
    // Combine all resistances into one array
    let allResistances = [];
    if (effectiveness.resistances) allResistances = allResistances.concat(effectiveness.resistances);
    if (effectiveness.double_resistances) allResistances = allResistances.concat(effectiveness.double_resistances);
    if (effectiveness.triple_resistances) allResistances = allResistances.concat(effectiveness.triple_resistances);
    // Sort by multiplier ascending (triple, double, single)
    allResistances.sort((a, b) => a[1] - b[1]);
    if (allResistances.length > 0) {
        allResistances.forEach(([type, mult]) => {
            let resistClass = '';
            if (Math.abs(mult - 0.244) < 0.01) resistClass = 'resist-triple';
            else if (Math.abs(mult - 0.391) < 0.01) resistClass = 'resist-double';
            else if (Math.abs(mult - 0.625) < 0.01) resistClass = 'resist-single';
            resistancesHtml += `<span class="type-badge type-${type} ${resistClass}" title="${mult}x">${type} (${mult}x)</span> `;
        });
    } else {
        resistancesHtml = '<span class="none">None</span>';
    }
    // Update the DOM
    document.querySelector('.effectiveness-weaknesses').innerHTML = weaknessesHtml;
    document.querySelector('.effectiveness-resistances').innerHTML = resistancesHtml;
    // Remove double resistances section if present
    let doubleResistSection = document.querySelector('.effectiveness-double-resistances');
    if (doubleResistSection) doubleResistSection.style.display = 'none';
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
        // For opponent, show best moves from PvPoke rankings with better formatting
        // For team Pokémon, this function is not used (handled in updateTeamSlot)
        if (isOpponent) {
            // Get the best moveset from PvPoke rankings if available
            let bestMoves = [];
            
            if (currentOpponent && currentOpponent.pvpoke_moveset && currentOpponent.pvpoke_moveset.length > 0) {
                // Use PvPoke's recommended moveset
                const movesetNames = currentOpponent.pvpoke_moveset;
                console.log(`[DEBUG] Opponent PvPoke moveset:`, movesetNames);
                
                bestMoves = pvpMoves.filter(move => {
                    const moveNameUpper = move.name.toUpperCase().replace(/ /g, '_');
                    const isInMoveset = movesetNames.includes(moveNameUpper);
                    console.log(`[DEBUG] Checking opponent move ${move.name} (${moveNameUpper}) against moveset: ${isInMoveset}`);
                    return isInMoveset;
                });
                
                console.log(`[DEBUG] Found ${bestMoves.length} opponent moves from PvPoke moveset:`, bestMoves.map(m => m.name));
                
                // If we couldn't find all moves, fall back to the original logic
                if (bestMoves.length < 3) {
                    console.log(`[DEBUG] Not enough opponent moves found (${bestMoves.length}), falling back to original logic`);
                    const fastMoves = pvpMoves.filter(m => m.move_class === 'fast').slice(0, 1);
                    const chargedMoves = pvpMoves.filter(m => m.move_class === 'charged').slice(0, 2);
                    bestMoves = [...fastMoves, ...chargedMoves];
                }
            } else {
                // Fallback to original logic if no PvPoke moveset
                const fastMoves = pvpMoves.filter(m => m.move_class === 'fast').slice(0, 1);
                const chargedMoves = pvpMoves.filter(m => m.move_class === 'charged').slice(0, 2);
                bestMoves = [...fastMoves, ...chargedMoves];
            }
            
            html += `<div class="moves-pvp-header">Best PvP Moves</div>`;
            html += `<div class="moves-list-pvp">`;
            html += bestMoves.map(move => {
                let moveDetails = '';
                
                if (move.move_class === 'fast') {
                    // Fast move details
                    if (move.power && move.energyGain) {
                        moveDetails = `<span class="move-details">${move.power} damage, +${move.energyGain} energy</span>`;
                    } else if (move.power) {
                        moveDetails = `<span class="move-details">${move.power} damage</span>`;
                    }
                } else if (move.move_class === 'charged') {
                    // Charged move details
                    if (move.power && move.energy) {
                        const dpe = (move.power / move.energy).toFixed(2);
                        moveDetails = `<span class="move-details">${move.power} damage, ${move.energy} energy (DPE: ${dpe})</span>`;
                    } else if (move.dpe) {
                        moveDetails = `<span class="move-details">DPE: ${move.dpe}</span>`;
                    }
                }
                
                return `
                <div class="move-item" onclick="event.stopPropagation(); openMoveSelector(null, '${move.name}', '${move.move_class}')">
                    <div class="move-info">
                        <div class="move-header">
                            <span class="move-name">${move.name}</span>
                            <span class="type-badge type-${move.type}">${move.type}</span>
                            <span class="move-type">(${move.move_class === 'fast' ? 'Fast' : 'Charged'})</span>
                            <span class="move-edit-icon">✏️</span>
                        </div>
                        ${moveDetails ? `<div class="move-details">${moveDetails}</div>` : ''}
                    </div>
                </div>
                `;
            }).join('');
            html += `</div>`;
        }
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

// Help modal functions
function showHelpModal() {
    helpModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closeHelpModal() {
    helpModal.classList.add('hidden');
    document.body.style.overflow = ''; // Restore scrolling
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
                        <img class="modal-result-sprite" src="${pokemon.sprite}" alt="${pokemon.readable_name}" onerror="console.error('Failed to load modal sprite:', this.src)">
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
    
    // Determine if this is a team Pokémon or opponent
    let pokemon = null;
    let isOpponent = false;
    
    if (slotNumber !== null && slotNumber !== undefined) {
        // Team Pokémon
        pokemon = userTeam.find(p => p.slot === slotNumber);
        isOpponent = false;
    } else {
        // Opponent Pokémon
        pokemon = currentOpponent;
        isOpponent = true;
    }
    
    if (!pokemon) {
        console.error('No Pokémon found for move selector');
        return;
    }
    
    // Use only speciesId for API calls
    fetch(`/api/pokemon/${encodeURIComponent(pokemon.speciesId)}/moves`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert('Failed to load moves');
                return;
            }
            
            const moves = moveClass === 'fast' ? data.fast_moves : data.charged_moves;
            showMoveSelector(moves, currentMoveName, moveClass, isOpponent);
        })
        .catch(error => {
            console.error('Error loading moves:', error);
            alert('Failed to load moves');
        });
};

function showMoveSelector(moves, currentMoveName, moveClass, isOpponent = false) {
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
    
    // Update modal title to indicate if it's for opponent
    const modalTitle = modal.querySelector('.modal-header h3');
    if (modalTitle) {
        const pokemonName = isOpponent ? (currentOpponent ? currentOpponent.name : 'Opponent') : 'Team Pokémon';
        modalTitle.textContent = `Select ${moveClass === 'fast' ? 'Fast' : 'Charged'} Move for ${pokemonName}`;
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
    
    // Determine if this is a team Pokémon or opponent
    let pokemon = null;
    let isOpponent = false;
    
    if (slotNumber !== null && slotNumber !== undefined) {
        // Team Pokémon
        pokemon = userTeam.find(p => p.slot === slotNumber);
        isOpponent = false;
    } else {
        // Opponent Pokémon
        pokemon = currentOpponent;
        isOpponent = true;
    }
    
    if (!pokemon) {
        console.error('No Pokémon found for move selection');
        return;
    }
    
    // Use only speciesId for API calls
    fetch(`/api/pokemon/${encodeURIComponent(pokemon.speciesId)}/moves`)
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
            console.log(`[DEBUG] Replacing move: ${currentMoveName} with: ${selectedMove.name}`);
            console.log(`[DEBUG] Current pvp_moves:`, pokemon.pvp_moves.map(m => m.name));
            
            // First, update the PvPoke moveset to reflect the custom move
            if (pokemon.pvpoke_moveset && pokemon.pvpoke_moveset.length > 0) {
                const oldMoveNameUpper = currentMoveName.toUpperCase().replace(/ /g, '_');
                const newMoveNameUpper = selectedMove.name.toUpperCase().replace(/ /g, '_');
                const movesetIndex = pokemon.pvpoke_moveset.indexOf(oldMoveNameUpper);
                
                if (movesetIndex !== -1) {
                    pokemon.pvpoke_moveset[movesetIndex] = newMoveNameUpper;
                    console.log(`[DEBUG] Updated PvPoke moveset: ${oldMoveNameUpper} -> ${newMoveNameUpper}`);
                }
            }
            
            // Now update the pvp_moves array - replace the specific move that was clicked
            const moveIndex = pokemon.pvp_moves.findIndex(m => m.name === currentMoveName);
            console.log(`[DEBUG] Found move at index: ${moveIndex}`);
            
            if (moveIndex !== -1) {
                // Replace the specific move that was clicked
                pokemon.pvp_moves[moveIndex] = selectedMove;
                console.log(`[DEBUG] Replaced move at index ${moveIndex}: ${currentMoveName} -> ${selectedMove.name}`);
            } else {
                // If not found, this shouldn't happen, but add it to the appropriate position
                console.log(`[DEBUG] Move not found in pvp_moves, adding to ${moveClass} moves`);
                if (moveClass === 'fast') {
                    // Remove any existing fast moves first
                    pokemon.pvp_moves = pokemon.pvp_moves.filter(m => m.move_class !== 'fast');
                    pokemon.pvp_moves.unshift(selectedMove);
                } else {
                    // For charged moves, add it to the end
                    pokemon.pvp_moves.push(selectedMove);
                }
            }
            
            // Clean up any duplicate moves that might have been created
            const seenMoves = new Set();
            pokemon.pvp_moves = pokemon.pvp_moves.filter(move => {
                const key = `${move.name}-${move.move_class}`;
                if (seenMoves.has(key)) {
                    console.log(`[DEBUG] Removing duplicate move: ${move.name}`);
                    return false;
                }
                seenMoves.add(key);
                return true;
            });
            
            // Ensure we maintain the correct number of moves per class
            const fastMoves = pokemon.pvp_moves.filter(m => m.move_class === 'fast');
            const chargedMoves = pokemon.pvp_moves.filter(m => m.move_class === 'charged');
            
            // Keep only 1 fast move and 2 charged moves
            if (fastMoves.length > 1) {
                console.log(`[DEBUG] Too many fast moves (${fastMoves.length}), keeping only the first`);
                const firstFastMove = fastMoves[0];
                pokemon.pvp_moves = pokemon.pvp_moves.filter(m => m.move_class !== 'fast');
                pokemon.pvp_moves.unshift(firstFastMove);
            }
            
            if (chargedMoves.length > 2) {
                console.log(`[DEBUG] Too many charged moves (${chargedMoves.length}), keeping only the first 2`);
                const firstTwoChargedMoves = chargedMoves.slice(0, 2);
                pokemon.pvp_moves = pokemon.pvp_moves.filter(m => m.move_class !== 'charged');
                pokemon.pvp_moves.push(...firstTwoChargedMoves);
            }
            
            // Store custom moveset to track user changes
            if (!pokemon.customMoveset) {
                pokemon.customMoveset = {};
            }
            pokemon.customMoveset[moveClass] = selectedMove.name;
            console.log(`[DEBUG] Updated custom moveset:`, pokemon.customMoveset);
            
            console.log(`[DEBUG] Updated pvp_moves:`, pokemon.pvp_moves.map(m => m.name));
            console.log(`[DEBUG] Updated pvpoke_moveset:`, pokemon.pvpoke_moveset);
            
            // Update the UI based on whether it's team or opponent
            if (isOpponent) {
                // Update opponent Pokémon
                currentOpponent = pokemon;
                displayPokemonInfo(currentOpponent);
            } else {
                // Update team Pokémon in the userTeam array to ensure battle simulation uses updated moves
                const teamIndex = userTeam.findIndex(p => p.slot === slotNumber);
                if (teamIndex !== -1) {
                    userTeam[teamIndex] = pokemon;
                }
                
                // Update UI
                updateTeamSlot(slotNumber, pokemon);
                // Force refresh of all team slots to update DPE displays
                refreshTeamMovesDisplay();
            }
            
            closeMoveSelector();
            
            // Clear battle cache to force fresh simulations with new moves
            clearBattleCache();
            
            // Re-run battle simulations and team analysis
            if (userTeam.length > 0) {
                updateTeamAnalysis();
            }
            onSelectionChange().catch(error => {
                console.error('Error in onSelectionChange:', error);
            });
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
        console.log('Adding Pokemon:', pokemonName, 'to slot:', slotNumber);
        const response = await fetch(`/api/pokemon/${encodeURIComponent(pokemonName)}`);
        
        if (!response.ok) {
            console.error('API response not ok:', response.status, response.statusText);
            alert(`Failed to add Pokémon: ${response.status} ${response.statusText}`);
            return;
        }
        
        const data = await response.json();
        console.log('API response data:', data);
        
        if (data.error) {
            console.error('API returned error:', data.error);
            alert(`Failed to add Pokémon: ${data.error}`);
            return;
        }
        
        if (!data.name || !data.speciesId) {
            console.error('Missing required data:', data);
            alert('Failed to add Pokémon: Invalid data received');
            return;
        }

        // --- PATCH: Set default moves to PvPoke best moveset if available ---
        if (data.pvpoke_moveset && data.pvpoke_moveset.length > 0 && data.pvp_moves && data.pvp_moves.length > 0) {
            // Find the best fast and charged moves from PvPoke moveset
            const bestFastMove = data.pvp_moves.find(m => m.move_class === 'fast' && data.pvpoke_moveset.includes(m.name.toUpperCase().replace(/ /g, '_')));
            const bestChargedMoves = data.pvp_moves.filter(m => m.move_class === 'charged' && data.pvpoke_moveset.includes(m.name.toUpperCase().replace(/ /g, '_')));
            // If found, set as the first moves in pvp_moves
            let newPvpMoves = [];
            if (bestFastMove) newPvpMoves.push(bestFastMove);
            if (bestChargedMoves.length > 0) newPvpMoves = newPvpMoves.concat(bestChargedMoves);
            // Fill up to 1 fast + 2 charged if needed
            if (!bestFastMove) {
                const fallbackFast = data.pvp_moves.find(m => m.move_class === 'fast');
                if (fallbackFast) newPvpMoves.unshift(fallbackFast);
            }
            while (newPvpMoves.filter(m => m.move_class === 'charged').length < 2) {
                const fallbackCharged = data.pvp_moves.find(m => m.move_class === 'charged' && !newPvpMoves.includes(m));
                if (fallbackCharged) newPvpMoves.push(fallbackCharged);
                else break;
            }
            // Replace pvp_moves for this instance
            data.pvp_moves = newPvpMoves;
        }
        // --- END PATCH ---
        
        userTeam = userTeam.filter(p => p.slot !== slotNumber);
        userTeam.push({
            ...data,
            slot: slotNumber,
            name: data.name, // display name
            speciesId: data.speciesId // canonical ID for API calls
        });
        
        console.log('Updated userTeam:', userTeam);
        updateTeamSlot(slotNumber, data);
        updateTeamAnalysis();
        onSelectionChange().catch(error => {
            console.error('Error in onSelectionChange:', error);
        });
        
        // Update move rankings immediately if opponent is selected
        if (currentOpponent) {
            updateAllTeamSlotsWithMoveRankings();
        }
    } catch (error) {
        console.error('Error adding Pokemon to team:', error);
        alert(`Failed to add Pokémon: ${error.message}`);
    }
}

function updateTeamSlot(slotNumber, pokemon, movesEffectiveness = null, isBestCounter = false) {
    console.log('updateTeamSlot called with:', { slotNumber, pokemon: pokemon.name });
    
    const slot = document.querySelector(`[data-slot="${slotNumber}"]`);
    console.log('Found slot element:', slot);
    
    if (!slot) {
        console.error(`Team slot ${slotNumber} not found in DOM`);
        console.log('Available slots:', document.querySelectorAll('[data-slot]'));
        return;
    }
    
    slot.classList.add('filled');
    
    // Remove best counter class - it will be set by updateTeamSlotBorders
    slot.classList.remove('best-counter');
    
            // Generate moves HTML - use the actual moves that are currently selected
            // This ensures that when you change a move, it stays exactly as you selected it
            let movesHTML = '';
            if (pokemon.pvp_moves && pokemon.pvp_moves.length > 0) {
                // Use the actual moves that are currently in the Pokémon's pvp_moves array
                // This preserves any custom move selections the user has made
                const fastMoves = pokemon.pvp_moves.filter(m => m.move_class === 'fast');
                const chargedMoves = pokemon.pvp_moves.filter(m => m.move_class === 'charged');
                
                // Take the first fast move and first two charged moves (or all if less than 2)
                const bestMoves = [
                    ...fastMoves.slice(0, 1),
                    ...chargedMoves.slice(0, 2)
                ];
                
                console.log(`[DEBUG] Using actual moves for ${pokemon.name}:`, bestMoves.map(m => m.name));
        
        movesHTML = `
            <div class="team-moves-section">
                <div class="team-moves-list">
                    ${bestMoves.map(move => {
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
                        
                        // Calculate move ranking for charged moves only (against all available charged moves)
                        if (move.move_class === 'charged' && pokemon.pvp_moves) {
                            console.log(`[DEBUG] ${move.name} - Checking for DPE property:`, move.dpe, 'power:', move.power, 'energy:', move.energy);
                            
                            // Get ALL available charged moves for this Pokémon (not just currently selected ones)
                            // We need to fetch the full move list to rank against all options
                            let allChargedMoves = [];
                            
                            // First, try to get moves from the original data if available
                            if (pokemon.moves && pokemon.moves.length > 0) {
                                allChargedMoves = pokemon.moves.filter(m => m.move_class === 'charged' && (m.dpe || (m.power && m.energy)));
                                console.log(`[DEBUG] Using moves from pokemon.moves for ranking:`, allChargedMoves.map(m => m.name));
                            }
                            
                            // If no moves from original data, use pvp_moves but ensure we have all available options
                            if (allChargedMoves.length === 0) {
                                allChargedMoves = pokemon.pvp_moves.filter(m => m.move_class === 'charged' && (m.dpe || (m.power && m.energy)));
                                console.log(`[DEBUG] Using moves from pokemon.pvp_moves for ranking:`, allChargedMoves.map(m => m.name));
                            }
                            
                            // If we still don't have enough moves for ranking, try to get the full move list from the API
                            if (allChargedMoves.length <= 1 && pokemon.speciesId) {
                                console.log(`[DEBUG] Not enough moves for ranking, attempting to fetch full move list for ${pokemon.speciesId}`);
                                // This is a fallback - in a real implementation, we'd want to cache the full move list
                                // For now, we'll use what we have
                            }
                            
                            console.log(`[DEBUG] Ranking ${move.name} against ${allChargedMoves.length} total charged moves`);
                            
                            if (allChargedMoves.length > 1) {
                                // For charged moves, rank by DPE
                                const chargedMoves = allChargedMoves;
                                if (chargedMoves.length > 1) {
                                    // Calculate DPE for all charged moves (use effective DPE if opponent exists, otherwise base DPE)
                                    const moveRankings = chargedMoves.map(m => {
                                        let baseDpe;
                                        if (m.dpe) {
                                            baseDpe = parseFloat(m.dpe);
                                        } else if (m.power && m.energy) {
                                            baseDpe = parseFloat(m.power) / parseFloat(m.energy);
                                        } else {
                                            baseDpe = 0; // Fallback
                                        }
                                        const effectiveDpe = currentOpponent ? 
                                            parseFloat(calculateEffectiveDPE(m, currentOpponent, pokemon.types)) : 
                                            baseDpe;
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
                                        console.log(`[DEBUG] ${move.name} ranked ${currentMoveRank + 1}/${moveRankings.length} (${percentageDiff.toFixed(1)}% from best) - DPE: ${currentMove.effectiveDpe.toFixed(2)} vs best: ${bestMove.effectiveDpe.toFixed(2)}`);
                                        if (currentMoveRank === 0) {
                                            moveRankingClass = 'move-best';
                                            rankingBadge = '<span class="ranking-badge ranking-gold">🥇</span>';
                                            console.log(`[DEBUG] ${move.name} - ASSIGNED move-best class and gold badge`);
                                        } else if (percentageDiff >= -10) {
                                            // Within 10% of best - excellent
                                            moveRankingClass = 'move-excellent';
                                            rankingBadge = '<span class="ranking-badge ranking-silver">🥈</span>';
                                            console.log(`[DEBUG] ${move.name} - ASSIGNED move-excellent class and silver badge`);
                                        } else if (percentageDiff >= -25) {
                                            // Within 25% of best - good
                                            moveRankingClass = 'move-good';
                                            rankingBadge = '<span class="ranking-badge ranking-bronze">🥉</span>';
                                            console.log(`[DEBUG] ${move.name} - ASSIGNED move-good class and bronze badge`);
                                        } else if (percentageDiff >= -50) {
                                            // Within 50% of best - mediocre
                                            moveRankingClass = 'move-mediocre';
                                            rankingBadge = '<span class="ranking-badge ranking-mediocre">⚠️</span>';
                                            console.log(`[DEBUG] ${move.name} - ASSIGNED move-mediocre class and mediocre badge`);
                                        } else {
                                            // More than 50% worse than best - poor
                                            moveRankingClass = 'move-poor';
                                            rankingBadge = '<span class="ranking-badge ranking-poor">❌</span>';
                                            console.log(`[DEBUG] ${move.name} - ASSIGNED move-poor class and poor badge`);
                                        }
                                        
                                        // Add percentage indicator for non-best moves
                                        if (currentMoveRank > 0) {
                                            rankingBadge += `<span class="ranking-percentage">${percentageDiff.toFixed(1)}%</span>`;
                                        }
                                    } else {
                                        console.log(`[DEBUG] ${move.name} - Could not find move in rankings`);
                                    }
                                } else {
                                    console.log(`[DEBUG] ${move.name} - Only one charged move available, no ranking needed`);
                                }
                            } else {
                                console.log(`[DEBUG] ${move.name} - No charged moves with DPE available for ranking`);
                                // If this is the only charged move, give it a default "good" rating
                                if (allChargedMoves.length === 1) {
                                    moveRankingClass = 'move-good';
                                    rankingBadge = '<span class="ranking-badge ranking-bronze">🥉</span>';
                                    console.log(`[DEBUG] ${move.name} - Only charged move available, assigning default good rating`);
                                }
                            }
                        } else {
                            console.log(`[DEBUG] ${move.name} - Not a charged move or no pvp_moves available`);
                        }
                        
                        // Calculate if this move is significantly better (20% or more) than other moves
                        let significantBetterClass = '';
                        if (move.move_class === 'charged' && pokemon.pvp_moves) {
                            // Get ALL available charged moves for this Pokémon (not just currently selected ones)
                            let allChargedMoves = [];
                            
                            // First, try to get moves from the original data if available
                            if (pokemon.moves && pokemon.moves.length > 0) {
                                allChargedMoves = pokemon.moves.filter(m => m.move_class === 'charged' && (m.dpe || (m.power && m.energy)));
                                console.log(`[DEBUG] Using moves from pokemon.moves for significant better check:`, allChargedMoves.map(m => m.name));
                            }
                            
                            // If no moves from original data, use pvp_moves but ensure we have all available options
                            if (allChargedMoves.length === 0) {
                                allChargedMoves = pokemon.pvp_moves.filter(m => m.move_class === 'charged' && (m.dpe || (m.power && m.energy)));
                                console.log(`[DEBUG] Using moves from pokemon.pvp_moves for significant better check:`, allChargedMoves.map(m => m.name));
                            }
                            
                            if (allChargedMoves.length > 1) {
                                const moveRankings = allChargedMoves.map(m => {
                                    let baseDpe;
                                    if (m.dpe) {
                                        baseDpe = parseFloat(m.dpe);
                                    } else if (m.power && m.energy) {
                                        baseDpe = parseFloat(m.power) / parseFloat(m.energy);
                                    } else {
                                        baseDpe = 0; // Fallback
                                    }
                                    const effectiveDpe = currentOpponent ? 
                                        parseFloat(calculateEffectiveDPE(m, currentOpponent, pokemon.types)) : 
                                        baseDpe;
                                    return { move: m, effectiveDpe, baseDpe };
                                }).sort((a, b) => b.effectiveDpe - a.effectiveDpe);
                                
                                const currentMoveRank = moveRankings.findIndex(r => r.move.name === move.name);
                                const bestMove = moveRankings[0];
                                const currentMove = moveRankings[currentMoveRank];
                                
                                if (currentMoveRank >= 0 && currentMoveRank > 0) {
                                    // Calculate percentage difference from best
                                    const percentageDiff = ((currentMove.effectiveDpe - bestMove.effectiveDpe) / bestMove.effectiveDpe) * 100;
                                    
                                    // If this move is within 20% of the best, mark it as significantly better
                                    if (percentageDiff >= -20) {
                                        significantBetterClass = 'move-significantly-better';
                                        console.log(`[DEBUG] ${move.name} is significantly better (${percentageDiff.toFixed(1)}% from best) - adding green background`);
                                    }
                                }
                            }
                        }
                        
                        console.log(`[DEBUG] ${move.name} - moveRankingClass: "${moveRankingClass}", significantBetterClass: "${significantBetterClass}"`);
                        console.log(`[DEBUG] ${move.name} - Final HTML classes: "move-item ${moveRankingClass} ${significantBetterClass}"`);
                        console.log(`[DEBUG] ${move.name} - Ranking badge HTML: "${rankingBadge}"`);
                        return `
                            <div class="move-item ${moveRankingClass} ${significantBetterClass}" onclick="event.stopPropagation(); openMoveSelector('${slotNumber}', '${move.name}', '${move.move_class}')">
                                <div class="move-info">
                                    <div class="move-name">${rankingBadge}${move.name}</div>
                                    <div class="move-details">
                                        <span class="type-badge type-${move.type}">${move.type}</span>
                                        <span class="move-type">(${move.move_class === 'fast' ? 'Fast Move' : 'Charged Move'})</span>
                                        ${move.dpe ? `<span class="move-dpe">DPE: ${currentOpponent && move.move_class === 'charged' ? parseFloat(calculateEffectiveDPE(move, currentOpponent, pokemon.types)).toFixed(2) : move.dpe}${effectiveDpeDisplay}</span>` : (move.move_class === 'charged' && move.power && move.energy) ? `<span class="move-dpe">DPE: ${currentOpponent ? parseFloat(calculateEffectiveDPE(move, currentOpponent, pokemon.types)).toFixed(2) : (move.power / move.energy).toFixed(2)}${effectiveDpeDisplay}</span>` : ''}
                                        ${effectivenessHTML}
                                        <span class="move-edit-icon">✏️</span>
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
        console.log('[DEBUG] Looking for battle result for:', pokemon.name);
        console.log('[DEBUG] Available battle results:', window.currentBattleResults);
        
        const battleResult = window.currentBattleResults ? 
            window.currentBattleResults.find(result => {
                console.log('[DEBUG] Checking result:', result.teamPokemon.name, 'vs', pokemon.name);
                return result.teamPokemon.name === pokemon.name;
            }) : null;
        
        console.log('[DEBUG] Found battle result:', battleResult);
        if (battleResult) {
            console.log('[DEBUG] Battle result details:', {
                winner: battleResult.battleResult.winner,
                teamHp: battleResult.battleResult.p1_final_hp,
                opponentHp: battleResult.battleResult.p2_final_hp,
                battleRating: battleResult.battleResult.battle_rating
            });
        } else {
            console.log('[DEBUG] No battle result found for:', pokemon.name);
        }
        
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
                        <div class="battle-rating">Rating: ${(battleResult.battleResult.battle_rating * 100).toFixed(1)}%</div>
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
    
    if (slot) {
        slot.innerHTML = `
            <div class="slot-content">
                <div class="pokemon-in-slot">
                    <div class="pokemon-header-section">
                        <div class="pokemon-name">${pokemon.name}</div>
                        <img src="${pokemon.sprite}" alt="${pokemon.name}" onerror="console.error('Failed to load image:', this.src)" onload="console.log('Successfully loaded image:', this.src)">
                        <div class="pokemon-types">
                            ${pokemon.types.map(type => `<span class="type-badge type-${type}">${type}</span>`).join('')}
                        </div>
                    </div>
                    <div class="pokemon-moves-section">
                        ${movesHTML}
                        ${battleResultHTML}
                    </div>
                    <button class="remove-pokemon" onclick="removePokemonFromTeam('${slotNumber}')">×</button>
                </div>
            </div>
        `;
    } else {
        console.error(`Cannot update slot ${slotNumber} - element not found`);
    }
}

function removePokemonFromTeam(slotNumber) {
    userTeam = userTeam.filter(p => p.slot !== slotNumber);
    
    const slot = document.querySelector(`[data-slot="${slotNumber}"]`);
    if (slot) {
        slot.classList.remove('filled');
        slot.innerHTML = `
            <div class="slot-content">
                <div class="add-pokemon">
                    <span class="plus-icon">+</span>
                    <span class="add-text">Add Pokemon</span>
                </div>
            </div>
        `;
    } else {
        console.error(`Cannot remove from slot ${slotNumber} - element not found`);
    }
    
    updateTeamAnalysis();
    onSelectionChange().catch(error => {
        console.error('Error in onSelectionChange:', error);
    });
}

function updateTeamAnalysis() {
    const teamAnalysis = document.getElementById('teamAnalysis');
    
    if (!teamAnalysis) {
        console.error('teamAnalysis element not found');
        return;
    }
    
    if (userTeam.length === 0) {
        teamAnalysis.classList.add('hidden');
        return;
    }
    
    teamAnalysis.classList.remove('hidden');
    
    // Calculate team coverage
    const coverage = calculateTeamCoverage();
    displayTeamCoverage(coverage);
    
    // Calculate team weaknesses, strengths, and missing coverage
    calculateTeamWeaknesses();
    calculateTeamStrengths();
    calculateMissingCoverage();
    
    // Run battle simulations if there's a current opponent
    if (currentOpponent) {
        runBattleSimulations().catch(error => {
            console.error('Error running battle simulations:', error);
        });
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
                if (multiplier > 1.0) {
                    coverage[type].count++;
                    coverage[type].pokemon.push(pokemon.name);
                }
            });
        }
    });
    console.log('[DEBUG] Team Coverage:', coverage);
    return coverage;
}

function displayTeamCoverage(coverage) {
    const coverageGrid = document.getElementById('teamCoverage');
    
    if (!coverageGrid) {
        console.error('teamCoverage element not found');
        return;
    }
    
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

function calculateTeamWeaknesses() {
    const allTypes = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 
                     'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 
                     'dragon', 'dark', 'steel', 'fairy'];
    const teamWeaknesses = {};
    // For each type, check if it's super effective against any team member
    allTypes.forEach(attackingType => {
        let totalEffectiveness = 0;
        let affectedPokemon = [];
        userTeam.forEach(pokemon => {
            if (pokemon.effectiveness && pokemon.effectiveness.effectiveness) {
                const effectiveness = pokemon.effectiveness.effectiveness[attackingType] || 1;
                if (effectiveness > 1.0) {
                    totalEffectiveness += effectiveness;
                    affectedPokemon.push(pokemon.name);
                }
            }
        });
        if (totalEffectiveness > 0) {
            teamWeaknesses[attackingType] = {
                effectiveness: totalEffectiveness,
                affectedPokemon: affectedPokemon
            };
        }
    });
    // Display team weaknesses
    const weaknessesList = document.getElementById('teamWeaknesses');
    console.log('[DEBUG] Team Weaknesses:', teamWeaknesses);
    if (weaknessesList) {
        const weaknessesHTML = Object.entries(teamWeaknesses)
            .sort((a, b) => b[1].effectiveness - a[1].effectiveness)
            .map(([type, data]) => `
                <span class="type-badge type-${type}" title="Affects: ${data.affectedPokemon.join(', ')}">${type}</span>
            `).join('');
        weaknessesList.innerHTML = weaknessesHTML || '<div class="no-data">No major weaknesses</div>';
        console.log('Updated teamWeaknesses with:', weaknessesHTML);
    } else {
        console.error('teamWeaknesses element not found');
    }
}

function calculateTeamStrengths() {
    const allTypes = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 
                     'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 
                     'dragon', 'dark', 'steel', 'fairy'];
    
    const teamStrengths = {};
    
    // For each type, check if the team resists it well
    allTypes.forEach(attackingType => {
        let totalResistance = 0;
        let resistantPokemon = [];
        
        userTeam.forEach(pokemon => {
            if (pokemon.effectiveness && pokemon.effectiveness.effectiveness) {
                const effectiveness = pokemon.effectiveness.effectiveness[attackingType] || 1;
                if (effectiveness < 1) {
                    totalResistance += (1 - effectiveness);
                    resistantPokemon.push(pokemon.name);
                }
            }
        });
        
        if (totalResistance > 0) {
            teamStrengths[attackingType] = {
                resistance: totalResistance,
                resistantPokemon: resistantPokemon
            };
        }
    });
    
    // Display team strengths
    const strengthsList = document.getElementById('teamStrengths');
    if (strengthsList) {
        const strengthsHTML = Object.entries(teamStrengths)
            .sort((a, b) => b[1].resistance - a[1].resistance)
            .map(([type, data]) => `
                <span class="type-badge type-${type}" title="Resisted by: ${data.resistantPokemon.join(', ')}">${type}</span>
            `).join('');
        
        strengthsList.innerHTML = strengthsHTML || '<div class="no-data">No major resistances</div>';
    } else {
        console.error('teamStrengths element not found');
    }
}

function calculateMissingCoverage() {
    const allTypes = ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 
                     'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 
                     'dragon', 'dark', 'steel', 'fairy'];
    
    const missingTypes = [];
    
    // Check which types the team doesn't cover well
    allTypes.forEach(type => {
        let hasCoverage = false;
        
        userTeam.forEach(pokemon => {
            if (pokemon.effectiveness && pokemon.effectiveness.effectiveness) {
                const effectiveness = pokemon.effectiveness.effectiveness[type] || 1;
                if (effectiveness > 1) {
                    hasCoverage = true;
                }
            }
        });
        
        if (!hasCoverage) {
            missingTypes.push(type);
        }
    });
    
    // Display missing coverage
    const missingList = document.getElementById('missingCoverage');
    if (missingList) {
        const missingHTML = missingTypes.map(type => `
            <span class="type-badge type-${type}">${type}</span>
        `).join('');
        
        missingList.innerHTML = missingHTML || '<div class="no-data">Good coverage!</div>';
    } else {
        console.error('missingCoverage element not found');
    }
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
    
    .move-charge-details {
        font-size: 0.85em;
        color: #666;
        font-style: italic;
        margin-left: 8px;
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
    const opponentId = currentOpponent.speciesId || currentOpponent.name;
    const teamIds = userTeam.map(p => p.speciesId || p.name);
    try {
        const resp = await fetch('/api/matchup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ opponent: opponentId, team: teamIds })
        });
        const data = await resp.json();
        // Update left panel (opponent) with full type chart
        if (data.opponent_effectiveness) {
            displayEffectiveness(data.opponent_effectiveness);
        }
        // Update right panel (team) with full type chart for each member
        if (data.team_infos && Array.isArray(data.team_infos)) {
            userTeam.forEach((pokemon, idx) => {
                if (data.team_infos[idx] && data.team_infos[idx].effectiveness) {
                    pokemon.effectiveness = data.team_infos[idx].effectiveness;
                }
            });
            // Recalculate team analysis panels
            updateTeamAnalysis();
        }
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
    
    if (multiplier === 0) {
        return { label: 'Immune', multiplier: 0 };
    } else if (multiplier > 1) {
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
        // Only show opponent's best PvP moves (from pvpoke_moveset)
        let bestMoveNames = [];
        if (currentOpponent && currentOpponent.pvpoke_moveset && currentOpponent.pvpoke_moveset.length > 0) {
            bestMoveNames = currentOpponent.pvpoke_moveset.map(m => m.replace(/_/g, ' ').toLowerCase());
        }
        // Filter the columns to only those moves
        let filteredOpponentMoves = opponentMovesVsTeam.filter(row => {
            const moveNameLower = row.move.name.toLowerCase();
            return bestMoveNames.includes(moveNameLower);
        });
        // Fallback: if no best moves found, show the first 3 moves
        if (filteredOpponentMoves.length === 0) {
            filteredOpponentMoves = opponentMovesVsTeam.slice(0, 3);
        }
        console.log('[DEBUG] Opponent moves shown in matchup table:', filteredOpponentMoves.map(r => r.move.name));
        // Table header: Opponent's moves
        html += `<table class="matchup-table"><thead><tr><th>Your Pokémon</th>`;
        filteredOpponentMoves.forEach(row => {
            html += `<th><span class="move-name">${row.move.name}</span><br><span class="type-badge type-${row.move.type}">${row.move.type}</span><br><span class="move-type">(${row.move.move_class})</span></th>`;
        });
        html += `</tr></thead><tbody>`;
        // Table rows: Your team
        teamNames.forEach((teamName, teamIndex) => {
            html += `<tr><td><strong>${teamName}</strong></td>`;
            filteredOpponentMoves.forEach(row => {
                const cell = row.vs_team[teamIndex];
                let effClass = '';
                if (cell.effectiveness.label === 'Super Effective') effClass = 'move-eff-super';
                else if (cell.effectiveness.label === 'Not Very Effective') effClass = 'move-eff-notvery';
                else if (cell.effectiveness.label === 'Immune') effClass = 'move-eff-immune';
                else effClass = 'move-eff-neutral';
                html += `<td><span class="move-effectiveness ${effClass}">${cell.effectiveness.label}</span>`;
                html += ` <span class="move-multiplier">(${cell.effectiveness.multiplier}x)</span>`;
                html += `</td>`;
            });
            html += `</tr>`;
        });
        html += `</tbody></table>`;
    }
    let matchupTable = document.getElementById('opponentMatchupTable');
    if (!matchupTable) {
        const analysisContent = document.querySelector('.analysis-content');
        matchupTable = document.createElement('div');
        matchupTable.id = 'opponentMatchupTable';
        analysisContent.prepend(matchupTable);
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

function updateAllTeamSlotsWithMoveRankings() {
    // This function specifically updates team slots to show move rankings
    userTeam.forEach(pokemon => {
        updateTeamSlot(pokemon.slot, pokemon, null, false);
    });
}

async function onSelectionChange() {
    if (currentOpponent && userTeam.length > 0) {
        await runBattleSimulations();
        await updateMatchupAnalysis(); // Add matchup analysis
        
        // Update all team slots to show move rankings and effectiveness with opponent context
        userTeam.forEach(pokemon => {
            updateTeamSlot(pokemon.slot, pokemon, null, false);
        });
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
            runBattleSimulations().catch(error => {
                console.error('Error running battle simulations:', error);
            });
            // Update move rankings and effectiveness since shield count affects effective DPE
            userTeam.forEach(pokemon => {
                updateTeamSlot(pokemon.slot, pokemon, null, false);
            });
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
        console.log('Using speciesIds:', teamPokemon.speciesId, currentOpponent.speciesId);

        try {
            // Use the actual moves from the Pokémon data (including custom movesets)
            let teamMoves = teamPokemon.pvp_moves || [];
            console.log(`[BATTLE DEBUG] Team moves for ${teamPokemon.name}:`, teamMoves.map(m => `${m.name} (${m.move_class})`));
            if (!teamMoves || teamMoves.length === 0) {
                console.log(`No PvP moves found for ${teamPokemon.name}`);
                continue;
            }

            // Use the actual moves from the opponent data (including custom movesets)
            let opponentMoves = currentOpponent.pvp_moves || [];
            console.log(`[BATTLE DEBUG] Opponent moves for ${currentOpponent.name}:`, opponentMoves.map(m => `${m.name} (${m.move_class})`));
            if (!opponentMoves || opponentMoves.length === 0) {
                console.log(`No PvP moves found for ${currentOpponent.name}`);
                continue;
            }

            // Run battle simulation
            const battleResult = await runSingleBattle(
                teamPokemon, teamMoves,
                currentOpponent, opponentMoves,
                shieldCount,
                battleSimulationState.shieldAI,
                battleSimulationState.shieldAI
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

// Only fetch by speciesId, never normalize from display name
async function getPvPMovesForPokemon(speciesId) {
    try {
        console.log(`Getting PvP moves for speciesId: ${speciesId}`);
        let response = await fetch(`/api/pokemon/${speciesId}`);
        let data = await response.json();
        if (data.error) {
            console.error(`Error fetching PvP moves for ${speciesId}:`, data.error);
            return [];
        }
        const pvpMoves = data.pvp_moves || [];
        console.log(`PvP moves for ${speciesId}:`, pvpMoves);
        return pvpMoves;
    } catch (error) {
        console.error(`Error getting PvP moves for ${speciesId}:`, error);
        return [];
    }
}

async function runSingleBattle(teamPokemon, teamMoves, opponentPokemon, opponentMoves, shieldCount, p1ShieldAI, p2ShieldAI) {
    console.log('Running single battle with:', { teamPokemon, teamMoves, opponentPokemon, opponentMoves, shieldCount });
    
    // Prepare battle data using the same "best moves" logic as the UI
    let teamFastMove, teamChargedMoves, opponentFastMove, opponentChargedMoves;
    
    // For team Pokémon - use the actual moves that are currently selected (no PvPoke filtering)
    // This ensures battle simulation uses the moves the user actually selected
    teamFastMove = teamMoves.find(m => m.move_class === 'fast');
    
    // Get the charged moves that are actually being used
    // IMPORTANT: Use the moves that are actually displayed in the UI, not the original teamMoves
    teamChargedMoves = [];
    
    // If the Pokémon has custom moveset, use those moves
    if (teamPokemon.customMoveset && teamPokemon.customMoveset.charged) {
        // Find the custom charged move in the available moves
        const customMove = teamMoves.find(m => m.move_class === 'charged' && m.name === teamPokemon.customMoveset.charged);
        if (customMove) {
            teamChargedMoves.push(customMove);
            console.log('[BATTLE DEBUG] Using custom charged move:', customMove.name);
        }
    }
    
    // Add the remaining charged moves (up to 2 total)
    const remainingChargedMoves = teamMoves.filter(m => m.move_class === 'charged' && 
        (!teamPokemon.customMoveset || m.name !== teamPokemon.customMoveset.charged));
    
    for (let i = 0; i < remainingChargedMoves.length && teamChargedMoves.length < 2; i++) {
        teamChargedMoves.push(remainingChargedMoves[i]);
    }
    
    console.log('[BATTLE DEBUG] Final team charged moves:', teamChargedMoves.map(m => m.name));
    
    // For opponent Pokémon - use the actual moves that are currently selected (no PvPoke filtering)
    // This ensures battle simulation uses the moves that are actually displayed in the UI
    opponentFastMove = opponentMoves.find(m => m.move_class === 'fast');
    opponentChargedMoves = opponentMoves.filter(m => m.move_class === 'charged').slice(0, 2);

    console.log('[BATTLE DEBUG] Selected moves for battle:', {
        teamFastMove: teamFastMove ? `${teamFastMove.name} (${teamFastMove.move_class})` : 'None',
        teamChargedMoves: teamChargedMoves.map(m => `${m.name} (${m.move_class})`),
        opponentFastMove: opponentFastMove ? `${opponentFastMove.name} (${opponentFastMove.move_class})` : 'None',
        opponentChargedMoves: opponentChargedMoves.map(m => `${m.name} (${m.move_class})`)
    });
    console.log('[BATTLE DEBUG] Team custom moveset:', teamPokemon.customMoveset);

    // Use speciesId for API calls (handles alternate forms correctly)
    let teamId = teamPokemon.speciesId || teamPokemon.name;
    let opponentId = opponentPokemon.speciesId || opponentPokemon.name;
    
    // Handle alternate forms by converting names to speciesId format
    if (teamPokemon.name.includes('(') && !teamId.includes('_')) {
        teamId = teamPokemon.name.toLowerCase()
            .replace('(', '')
            .replace(')', '')
            .replace(' ', '_')
            .replace('galarian', 'galar')  // Keep as 'galarian', not 'galar'
            .replace('alolan', 'alola')      // Keep as 'alolan', not 'alola'
            .replace('hisuian', 'hisuian');   // Keep as 'hisuian', not 'hisui'
    }
    
    if (opponentPokemon.name.includes('(') && !opponentId.includes('_')) {
        opponentId = opponentPokemon.name.toLowerCase()
            .replace('(', '')
            .replace(')', '')
            .replace(' ', '_')
            .replace('galarian', 'galar')  // Keep as 'galarian', not 'galar'
            .replace('alolan', 'alola')      // Keep as 'alolan', not 'alola'
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
        p2_shields: shieldCount,
        p1_shield_ai: p1ShieldAI || 'smart_30',
        p2_shield_ai: p2ShieldAI || 'smart_30',
        cp_cap: battleSimulationState.cpCap
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
    console.log('[DEBUG] displayBattleSimulations called with results:', results);
    
    // Store results globally for team slots to access
    window.currentBattleResults = results;
    console.log('[DEBUG] Stored battle results globally:', window.currentBattleResults);
    
    // Update all team slots to show battle results
    userTeam.forEach(pokemon => {
        console.log('[DEBUG] Updating team slot for:', pokemon.name, 'in slot:', pokemon.slot);
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

// Clear battle cache when league changes
function clearBattleCache() {
    battleSimulationState.simulations = {};
    console.log('Battle cache cleared');
}

// Initialize league selector and shield AI selector
function initLeagueAndShieldSelectors() {
    const leagueSelect = document.getElementById('leagueSelect');
    const shieldAI = document.getElementById('shieldAI');
    
    if (leagueSelect) {
        // Set initial value
        leagueSelect.value = battleSimulationState.cpCap || 1500;
        
        // Add event listener
        leagueSelect.addEventListener('change', function() {
            const selectedCP = parseInt(this.value);
            battleSimulationState.cpCap = selectedCP;
            console.log('League changed to:', selectedCP);
            
            // Clear any cached data that might be CP-specific
            clearBattleCache();
            
            // Trigger battle simulation update if we have an opponent
            if (currentOpponent && userTeam.length > 0) {
                runBattleSimulations().catch(error => {
                    console.error('Error running battle simulations:', error);
                });
            }
        });
    }
    
    if (shieldAI) {
        // Set initial value
        shieldAI.value = battleSimulationState.shieldAI || 'smart_30';
        
        // Add event listener
        shieldAI.addEventListener('change', function() {
            battleSimulationState.shieldAI = this.value;
            console.log('Shield AI changed to:', this.value);
            // Trigger battle simulation update if we have an opponent
            if (currentOpponent && userTeam.length > 0) {
                runBattleSimulations().catch(error => {
                    console.error('Error running battle simulations:', error);
                });
            }
        });
    }
}

// Initialize battle simulations when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // ... existing initialization code ...
    
    initBattleSimulations();
    
    // Initialize league and shield AI selectors
    initLeagueAndShieldSelectors();
}); 