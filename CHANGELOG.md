# Changelog

All notable changes to The Dragon Rises are listed here, newest first.

## Version names

Every release gets a Welsh name, taken from a different theme for each kind of update:

| Update type | Example | Named after | Next names, in order |
|---|---|---|---|
| Major | 1.0.0 | Welsh princes and kings | Glyndŵr, Llywelyn, Hywel Dda, Rhodri Mawr, Gruffudd ap Cynan |
| Minor | 0.1.0 | Welsh castles | ~~Caernarfon~~, ~~Harlech~~, Conwy, Beaumaris, Castell Coch, Pembroke, Cilgerran |
| Patch | 0.0.1 | Welsh rivers | Taf, Tywi, Teifi, Wysg, Conwy, Dyfrdwy, Hafren |

Take the next unused name from the row for that update type, and strike it through here once it's used. 1.0.0 is reserved as **"Glyndŵr"**, after the last native Prince of Wales.

## [0.2.0] "Harlech" - Unreleased

This release makes every political path playable, fixes many features that were silently broken, and brings Wales's power level back in line with a single-state nation.

### Added

- **Choosing a path.** Completing *Choose Our Path* now opens the event "Which Way for Cymru?", where you choose Democracy, Revolution, Nationalism, Monarchy or Reunion. Your choice unlocks that path's first focus and boosts its ideology's popularity. Before this, only the Democratic and Reunion paths could be started.
- **Seizing power.** The Communist path ends in a general strike (*The Red Flag over Cardiff*) and the Fascist path in a coup (*The March on Cardiff*). Each puts its party and leader in charge.
- **Coronation.** New *Crown the King* decision puts King Owain IV on the throne and is followed by the Coronation event.
- **Celtic Union diplomacy.** New *Offer Union to Ireland / Scotland* decisions. If they think well of Wales, they may accept becoming a subject, which makes *Form the Celtic Union* possible for the first time.
- **UK Reunion events.** Britain now responds to Wales's request to rejoin, either welcoming or rebuffing the delegation.
- New decisions that were already promised in focus tooltips but missing:
  - *Establish Workers' Councils*
  - *Aid the Red Clydeside*
  - *Aid the Irish Workers*
  - *Purge Dissidents*
  - *Strengthen the Druidic Order*
- New *Fortress Wales* national spirit for the *Impregnable Fortress* focus.
- Flavour events for exporting the revolution and for the British revolution.

### Changed

- **National spirits now upgrade instead of piling up.** Later focuses replace earlier spirits and include their bonuses, for example *A Democratic Mandate* → *Welsh National Assembly* and *Rise of the Dragon* → *Purging British Influence*. Expect far fewer spirits on screen.
- **Rebalanced industry.** Free off-map factories and resources from focuses and decisions have been cut to roughly a third. Examples:
  - *Total War Economy*: 15 → 5 military factories
  - *Total Nationalization*: 10 civilian + 8 military → 3 + 3
  - *Seek UK Investment*: 8 civilian + 4 military → 3 + 1
  - *Fortress Wales Complete*: 5 civilian + 5 military + 3 dockyards → 2 + 2 + 1
- **Rebalanced political power.** The opening spirits of each path now give +15% political power gain, down from +50% to +100%.
- **Decisions can only be taken once.** Ten decisions that could previously be repeated forever now fire once, including the free-division decisions and *Coal Empire* (infinite steel and tungsten). Manpower from the division decisions is reduced from 50,000–75,000 to 20,000–25,000.
- *Mass Industrialization*, *Military-Industrial Complex* and *Coal Empire* are now unlocked by their industrial-branch focuses on every path. Before, *Mass Industrialization* was Democratic-only and *Coal Empire* was available from day one.
- The 53rd (Welsh) Infantry Division has been removed from the British army.

### Fixed

- **None of the decisions worked.** The decision file was structured incorrectly, so the game did not recognise any decision. All decisions now appear in their category.
- The UK Reunion focus fired an event that did not exist.
- Two focuses gave national spirits that did not exist.
- Taking *Negotiate Reunion* did not lock out the other paths.
- *Royal Navy Protection* appeared under the Democratic branch instead of the Reunion branch.
- Coastal bunkers and naval bases were placed on inland border provinces.
- The *Dominance of the Celtic Isles* focus tried to declare war on Scotland, which doesn't exist in 1936.
- Wales started with no army, because the starting unit files were not being loaded.
- Fixed a broken leader trait file, a broken focus icon definition, and invalid buildings in Wales's country history.
- Fixed missing icons on the Reunion national spirits and an invalid training-time modifier.

### For contributors

- New `tools/check_mod.py` checks the mod for structural errors, missing references and missing localisation. It runs automatically on every push via GitHub Actions.
- VS Code now recommends the CWTools extension for full validation against vanilla HOI4.

### Known issues

- Leader portraits are still placeholders.
- Decision category icons have not yet been verified in game.
- The Celtic Empire and Celtic Union cosmetic tags have no flags yet.

## [0.1.0] "Caernarfon" - Alpha

- First public alpha: five political paths, an industrial and fortress branch, custom characters, national spirits, decisions and English localisation.
