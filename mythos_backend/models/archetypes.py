"""
Archetype definitions — 22 storytelling frameworks.

Each framework maps archetype names to their definitions.
The semantic scorer matches character descriptions against these.
"""

ARCHETYPE_DEFINITIONS: dict[str, dict[str, str]] = {
    "Jungian": {
        "Hero": "The protagonist, usually driven by a mission to save the day.",
        "Shadow": "The dark side, representing repressed traits and the unknown potential.",
        "Anima/Animus": "The unconscious feminine/masculine qualities that influence the opposite gender in the ego.",
        "Wise Old Man/Woman": "The guide or sage, offering wisdom and a solution to the central dilemma.",
    },
    "Disney": {
        "The Dreamer": "An optimistic character who believes in magic, wishes, and the power of dreams to transform reality.",
        "The Villain": "A charismatic antagonist driven by vanity, greed, or a desire for control, often with tragic backstory.",
        "The Sidekick": "A loyal companion providing comic relief, emotional support, and unexpected wisdom at key moments.",
        "The Mentor": "A wise guide who sacrifices or steps back to let the protagonist discover their own strength.",
    },
    "James Cameron": {
        "The Warrior": "A battle-hardened fighter who discovers humanity through connection and sacrifice.",
        "The Corporate Antagonist": "A ruthless, profit-driven entity that exploits nature or technology without moral restraint.",
        "The Indigenous Sage": "A character deeply connected to nature/tradition, representing harmony and ecological balance.",
        "The Tech Operator": "A skilled pilot or technician who bridges humanity and advanced technology/machinery.",
    },
    "General": {
        "The Everyman": "An ordinary person thrust into extraordinary circumstances, relatable and grounded.",
        "The Mentor": "A guide figure who provides wisdom, training, or magical assistance to the protagonist.",
        "The Trickster": "A cunning character who bends rules, providing chaos that ultimately serves a greater purpose.",
        "The Guardian": "A protector whose loyalty and strength shield others, often at great personal cost.",
    },
    "Fantasy": {
        "The Chosen One": "Destined hero with latent magical powers, often marked by prophecy or birthright.",
        "The Dark Lord": "An ancient evil seeking dominion, representing corruption of power and immortality's curse.",
        "The Quest Companion": "A diverse ally bringing unique skills (warrior, mage, rogue) essential to the journey.",
        "The Wise Wizard": "An ancient magic user who understands the balance between light and dark, order and chaos.",
    },
    "Gothic": {
        "The Haunted Soul": "A tormented character pursued by past sins, supernatural forces, or family curses.",
        "The Byronic Hero": "A brooding, isolated figure with a dark past, attractive yet dangerous and morally ambiguous.",
        "The Innocent": "A pure character whose presence exposes the corruption around them, often leading to tragedy.",
        "The Ancestral Curse": "A legacy of darkness passed through bloodlines, binding characters to inherited doom.",
    },
    "Dark Gothic": {
        "The Vampire": "An immortal predator representing seduction, eternal hunger, and the horror of unending existence.",
        "The Mad Scientist": "An obsessive genius who transgresses natural boundaries, creating monsters through forbidden knowledge.",
        "The Ghost": "A restless spirit bound to a location or person, unable to move on due to unresolved trauma.",
        "The Corrupted Priest": "A fallen religious figure whose faith twisted into fanaticism, hypocrisy, or demonic possession.",
    },
    "Romance": {
        "The Star-Crossed Lover": "A passionate character whose love is forbidden by society, fate, or circumstance.",
        "The Protector": "Someone who falls in love while guarding or rescuing another, torn between duty and desire.",
        "The Rival-to-Lover": "An antagonist whose opposition masks attraction, creating tension that transforms into romance.",
        "The Second Chance": "A character seeking redemption through love, haunted by past relationship failures or losses.",
    },
    "Mystery": {
        "The Detective": "A brilliant investigator driven by justice, logic, and an obsessive need to solve puzzles.",
        "The Red Herring": "A character designed to mislead, whose suspicious behavior conceals innocence or irrelevance.",
        "The Hidden Culprit": "An unexpected villain whose ordinary facade masks guilt, motive perfectly concealed.",
        "The Witness": "Someone who knows crucial information but is silenced, threatened, or unreliable due to trauma.",
    },
    "Adventure": {
        "The Explorer": "A fearless adventurer driven by discovery, treasure, or the thrill of the unknown.",
        "The Reluctant Hero": "An ordinary person forced into danger, growing into courage through trials and necessity.",
        "The Rival Adventurer": "A competing treasure hunter or explorer whose methods clash but goals may align.",
        "The Local Guide": "A native expert whose knowledge of terrain, culture, or danger becomes essential for survival.",
    },
    "Norse": {
        "The Berserker": "A warrior consumed by battle rage, channeling primal fury at the cost of control and sanity.",
        "The Völva": "A seeress who reads fate through runes and visions, bound by the immutable threads of wyrd.",
        "The Oath-Breaker": "One cursed by broken vows, hunted by gods and men, seeking impossible redemption.",
        "The Skald": "A poet-warrior whose words shape reality, preserving glory or casting curses through saga.",
    },
    "Mythological": {
        "The Demigod": "Half-mortal, half-divine, struggling between human weakness and godly ambition.",
        "The Titan": "An ancient primordial force representing chaos, nature, or primal power before civilization.",
        "The Oracle": "A conduit for prophecy whose visions burden them with knowledge they cannot change.",
        "The Trickster God": "A divine shapeshifter who disrupts order, teaching through chaos and deception.",
    },
    "Greek": {
        "The Tragic Hero": "A noble figure whose fatal flaw (hamartia) leads to inevitable downfall despite good intentions.",
        "The Fury": "A vengeful spirit embodying divine retribution, punishing hubris and injustice without mercy.",
        "The Philosopher-King": "A wise ruler who governs through reason, justice, and understanding of truth.",
        "The Labyrinth Keeper": "Guardian of mysteries and forbidden knowledge, testing heroes through impossible trials.",
    },
    "Horror": {
        "The Final Girl": "A survivor whose moral purity and resourcefulness allow escape from unspeakable evil.",
        "The Harbinger": "A cryptic stranger who warns of coming doom, ignored until it's too late.",
        "The Possessed": "An innocent vessel corrupted by malevolent force, losing autonomy to darkness.",
        "The Unseen Terror": "An entity whose true form remains hidden, more terrifying for what isn't shown.",
    },
    "Sci-Fi": {
        "The Synthetic": "An artificial being questioning consciousness, humanity, and the nature of existence.",
        "The Xenobiologist": "A scientist bridging humanity and alien life, translating the incomprehensible.",
        "The Post-Human": "An evolved or augmented being who has transcended biological limitations.",
        "The Time Paradox": "A character caught in causal loops, their actions creating their own existence or doom.",
    },
    "Quantum Physics": {
        "The Observer": "One whose perception collapses probability waves, making reality through observation.",
        "The Entangled": "Two beings connected across space-time, sharing states and fates instantaneously.",
        "The Superposition": "A character existing in multiple states simultaneously until forced to choose one path.",
        "The Uncertainty": "Someone who cannot know both position and momentum, perpetually incomplete in understanding.",
    },
    "Medieval": {
        "The Knight-Errant": "A wandering warrior bound by chivalric code, seeking worthy quests and honorable combat.",
        "The Sovereign": "A monarch balancing divine right, feudal duty, and the burden of the crown.",
        "The Heretic": "A truth-seeker branded blasphemer, challenging church doctrine at peril of stake.",
        "The Plague Doctor": "A healer walking the line between medicine and superstition amid death's shadow.",
    },
    "C.S. Lewis": {
        "The Redeemed Sinner": "A flawed character saved by grace, transformed through sacrifice and unconditional love.",
        "The Aslan Figure": "A Christ-like sacrificial hero whose death brings resurrection and restoration.",
        "The Pevensie": "An ordinary person called to extraordinary destiny, growing through trials in a magical realm.",
        "The Screwtape": "A tempter who reveals evil's banality through bureaucratic corruption of virtue.",
    },
    "Stephen King": {
        "The Small-Town Everyman": "An ordinary person in a familiar setting confronting supernatural or cosmic horror.",
        "The Psychic Child": "A young protagonist with paranormal gifts, vulnerable yet powerful against evil.",
        "The Corrupted Writer": "An artist whose creativity becomes a conduit for darkness, obsession, or madness.",
        "The Returned": "Someone who came back wrong — from death, the past, or another realm — bringing trauma.",
    },
    "Alfred Hitchcock": {
        "The Wrong Man": "An innocent caught in circumstances beyond control, paranoia mounting as escape narrows.",
        "The Blonde": "A cool, elegant figure concealing dark secrets or dangerous obsessions beneath grace.",
        "The Voyeur": "An observer whose watching crosses ethical lines, implicated in the horror they witness.",
        "The Mother": "A dominating maternal figure whose love becomes suffocating control or psychological prison.",
    },
    "Japanese": {
        "The Ronin": "A masterless samurai torn between honor and survival, seeking purpose after losing their lord.",
        "The Yokai": "A supernatural spirit — trickster, guardian, or vengeful — embodying nature's mysterious power.",
        "The Salary Man": "A modern archetype ground down by corporate duty, seeking meaning in conformity's cracks.",
        "The Onryo": "A vengeful ghost bound by wrongful death, unable to rest until justice or revenge.",
    },
    "Korean": {
        "The Han-Bearer": "One carrying deep sorrow (han) from historical trauma, injustice, or generational pain.",
        "The Chaebol Heir": "A privileged successor to corporate dynasty, torn between duty and personal desire.",
        "The Mudang": "A shaman mediating between living and dead, channeling spirits through ritual and trance.",
        "The Jeong-Keeper": "Someone bound by deep emotional connection (jeong), loyalty transcending logic or self.",
    },
}
