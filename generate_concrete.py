#!/usr/bin/env python3
"""
Generate a massive, high-quality list of concrete English nouns.

Definition of "concrete noun" for this list:
  A word that refers to a physical thing that can be represented as an object.
  Includes: physical objects, animals, plants, foods, tools, vehicles,
  buildings, clothing, body parts, natural features, materials, substances,
  celestial bodies, people (as physical beings).
  Excludes: actions, processes, events, states, emotions, qualities,
  measurements, time periods, ideas, relations, communications, abstract
  legal/social/linguistic/psychological concepts.

Strategy:
  1. Pull every single-word noun from WordNet.
  2. Keep only words that have AT LEAST ONE sense under physical_entity
     and do NOT have their primary sense under abstraction.
  3. Apply a large manual blacklist of abstract words the hypernym test
     sneaks through (e.g. sin, niche, shift, access, addition).
  4. Reject words that appear in NO common corpus (Brown + existing list +
     curated extras) — this strips obscure taxonomic/archaic terms that
     are concrete but no English speaker has ever heard.
  5. Supplement with a large curated list of common everyday concrete
     objects that might be missing.
  6. Apply profanity filter.
"""

import ssl, json, re, sys
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

import nltk
from nltk.corpus import wordnet as wn

def _ensure_corpus(name):
    try:
        c = getattr(__import__('nltk.corpus', fromlist=[name]), name)
        _ = c.words()[:1]
        return c
    except (LookupError, Exception):
        nltk.download(name, quiet=True)
        return getattr(__import__('nltk.corpus', fromlist=[name]), name)


brown = _ensure_corpus('brown')
gutenberg = _ensure_corpus('gutenberg')
reuters = _ensure_corpus('reuters')
webtext = _ensure_corpus('webtext')
movie_reviews = _ensure_corpus('movie_reviews')


# ========== Hypernym roots ==========

# Concrete roots: a word is "concrete-capable" only if a sense is under one
# of these. NB: we deliberately do NOT include physical_entity.n.01 itself,
# because WordNet puts process.n.06 (e.g. "absorption", "accretion") under
# physical_entity. We want real physical things only.
CONCRETE_ROOTS = {
    'object.n.01',
    'thing.n.12',
    'artifact.n.01',
    'natural_object.n.01',
    'living_thing.n.01',
    'organism.n.01',
    'matter.n.03',
    'substance.n.01',
    'food.n.01',
    'food.n.02',
    'plant.n.02',
    'animal.n.01',
    'person.n.01',
    'causal_agent.n.01',  # covers person + agent physical things
    'body_part.n.01',
    'location.n.01',
    'structure.n.01',
    'geological_formation.n.01',
    'celestial_body.n.01',
    'region.n.03',
    'body_of_water.n.01',
    'land.n.04',
    'atmospheric_phenomenon.n.01',
}

# If a sense is under any of these, we consider that sense abstract. Words
# whose primary sense is abstract get rejected.
ABSTRACT_ROOTS = {
    'abstraction.n.06',
    'psychological_feature.n.01',
    'attribute.n.02',
    'state.n.02',
    'state.n.04',
    'event.n.01',
    'act.n.02',
    'measure.n.02',
    'time_period.n.01',
    'time_unit.n.01',
    'relation.n.01',
    'communication.n.02',
    'content.n.05',
    'possession.n.02',
    'social_group.n.01',
    'group.n.01',
    'cognition.n.01',
    'feeling.n.01',
    'motivation.n.01',
    # Processes: "absorption", "accretion", "abduction", "abolition", etc.
    'process.n.06',
    'natural_process.n.01',
    'activity.n.01',
}


def get_all_hypernyms(synset):
    hyps = set()
    for path in synset.hypernym_paths():
        hyps.update(h.name() for h in path)
    return hyps


def concrete_score(word):
    """
    Return (has_concrete_sense, primary_is_abstract, concrete_fraction).
    has_concrete_sense: any sense is under CONCRETE_ROOTS and not purely abstract.
    primary_is_abstract: the first (most common) sense is abstract.
    concrete_fraction: what share of senses are concrete.
    """
    synsets = wn.synsets(word, pos=wn.NOUN)
    if not synsets:
        return False, True, 0.0

    concrete_senses = 0
    abstract_senses = 0
    primary_abstract = False

    for i, s in enumerate(synsets):
        hyps = get_all_hypernyms(s)
        is_conc = bool(hyps & CONCRETE_ROOTS)
        is_abs = bool(hyps & ABSTRACT_ROOTS) and not is_conc
        if is_conc:
            concrete_senses += 1
        elif is_abs:
            abstract_senses += 1
            if i == 0:
                primary_abstract = True

    total = concrete_senses + abstract_senses
    frac = concrete_senses / total if total else 0.0
    return concrete_senses > 0, primary_abstract, frac


# ========== Large manual blacklist ==========
# Abstract words that hypernym filtering lets through, or that we want
# to be extra sure never appear in "objects only" mode.

ABSTRACT_BLACKLIST = set("""
ability abnormality abolishment abortion abrogation absence abstinence
abundance abuse abyss acceptance accident accommodation accompaniment
accomplishment accord accordance accountability accounting accuracy
accusation achievement acknowledgment acquaintance acquisition acronym
act action activation activity adaptation addiction addition adherence
adjective adjustment admiration admission adolescence adoption adulthood
advance advancement advantage advent adventure adverb adversity advert
advertising advice advocacy affair affect affection affidavit affinity
affliction afterlife aftermath afternoon afterthought age agency agenda
aggression agony agreement aid aim air alarm alert alias alibi alimony
allegation allegiance allegory allergy alliance allocation allowance
allusion aloha altercation alternative altruism amalgamation amazement
ambiance ambience ambiguity ambition amendment amnesia amnesty amount
amusement anagram analgesia analogy analysis analytics anarchy ancestry
anecdote anger angle anguish animation anniversary announcement annoyance
anomaly answer anthem anthology anticipation antithesis anxiety apathy
apology apotheosis appeal appearance appellation appetite applause
application appointment appreciation apprehension approach appropriation
approval approximation april aptitude arbitration arcade archetype
architecture archives area argument arithmetic army arousal arrangement
arrest arrival arrogance art article artwork ascent aside aspect
aspersion aspiration assassination assault assembly assent assertion
assessment asset assignment assistance association assortment assumption
assurance asymmetry atmosphere atrocity attack attainment attempt
attendance attention attenuation attitude attraction attribute august
aura austerity authentication authenticity authority authorization
autobiography autonomy availability avenue average aversion award
awareness awe backdrop background backing backlash backlog backup
badge badness bail balance ballad ballet ballot balm ban band bandwidth
bang banishment bankruptcy banter bargain barrage barrier barter base
baseline basic basics basis batch bath bathe battle bearing beating
beauty becoming beckon beginner beginning behalf behavior behaviour
being belief believer belonging benefit benevolence benison bequest
bereavement bet betrayal betting biannual bias bicentennial bidding
billing biography biology biopsy birth birthday bit bite blackmail
blame blank blast blaze blessing bliss blockade blog blogpost blood
bloodshed blow blowback blueprint bluff blunder blur blush board
boast body bombardment bombing bond bondage bonding bonus boo booking
boolean boom boon boost border boredom borough boson bother bough
bounce boundary bounty bout boycott boyfriend boyhood brainchild
bravery breach break breakdown breakfast breakpoint breakthrough
breath breathing breed breeding breeze bribery brigade brightness
brilliance brochure bruise brunch brushwork brutality bubble budget
bug build buildup bulk bulletin bulling bullying bunch bundle burden
burial burn burnout burst bushido business buzz cadence calamity
calculation caliber calling callus calm campaign cancer candidacy
candor canon canter capability capacity capital captivity caption
capture cardinal care career case cash casino casino casting catalog
catastrophe catch cathedral cause caution ceasefire celebration
censorship census centennial ceremony certainty certification change
channel chant chaos character charge charity charm chart chase chat
chatter check checkup cheer childhood chill chimera chivalry choice
chord chore choreography chronicle chunk circuit circular circumcision
citation citizenship civics civilization claim clarity clash class
classification clause cleaning clearance cleft climax cling clip
clone close closing closure clout coaching coalition code coding
coincidence collapse collection collective collision colonization
column combat combination combustion comedy comfort coming command
commendation comment commentary commerce commission commitment
committee commodity common commotion communion community comparison
compass compensation competence competition complacency complaint
completion complexity compliance complication complicity component
composition compound comprehension compromise compulsion computation
concept conception concern concert concession conclusion concoction
concord concrete concurrence condition condolence conduct conference
confession confidence configuration confinement confirmation conflict
confluence conformity confrontation confusion congestion conglomerate
congratulations congress conjecture conjunction connection consciousness
consensus consent consequence conservation consideration consignment
consolation consolidation consortium conspiracy constitution
constraint construction consultation consumption contact contagion
containment contamination contemplation contempt content contention
contest context contingency continuation continuity continuum
contract contradiction contrast contribution control controversy
convenience convention conversation conversion conviction convocation
cooking cooperation coordination cope copyright corollary correction
correlation correspondence corridor corroboration corruption cost
costume count counter counterargument counterattack counterpart
country countryside coup courage course courtesy courtship cover
coverage coverup covetousness craze creation creativity credential
credibility credit creed crescendo crew crime crisis criterion
critic criticism critique crore crush cry cue culmination culpability
cult culture cumulus curiosity curl curse curvature custody custom
cutback cuteness cycle dab damage damnation dance dancing danger
daresay daring darkness data database date daub dawn day daybreak
daydream daylight daze deadline deadlock deal dealing dearth death
debacle debate debit debt debugging debut decade decay deceit
deception decibel decimal decision declaration decline decontamination
decor decorum decrease decree dedication deduction deed deference
deficiency deficit definition deformity defusing degradation degree
dejection delay delegation deletion deliberation delicacy delight
delinquency delivery demand democracy demo demographic demolition
demonstration demotion denial denouement denunciation dependability
dependence depiction deposition depreciation depression deprivation
depth deputation derailment descent description desertion design
desire despair desperation destination destiny destruction detail
detection detention detergent deterioration determination deterrent
detour detoxification detraction development deviation devotion
diagnosis diagonal diagram diameter diatribe dichotomy dictate
didactics differ difference differentiation difficulty dignity
dilemma diligence dilution dimension diminution direction directive
disability disadvantage disagreement disappearance disappointment
disapproval disarmament disaster disbelief discharge discipline
disclosure discomfort disconnection discontent discouragement
discovery discreet discretion discrimination discussion disdain
disease disgrace disgust dishonor disillusionment disincentive
disintegration dislike dismay dismissal disorder disorganization
disparity dispatch dispersal displacement display displeasure
disposal dispute disregard disrepute disruption dissatisfaction
dissemination dissension dissent dissertation dissolution dissonance
distance distinction distortion distraction distress distribution
distrust disturbance divergence diversification diversity division
divorce dizziness doctrine document documentation dogma dogmatism
domain domestication dominance domination donation doom doubt
downfall download downpour downside downstroke downtime downtrend
downturn draft drama drawback drawing dread dream drift drill
drive driving drop drought drowning drowsiness drudgery dub due
duo dues duel duration duress dusk dust duty dyeing dynamic eagerness
ease easiness economics economy ecstasy edge edit editing education
eeriness effect effectiveness efficacy efficiency effort ego
election electricity elegance element elevation elicitation
elimination elite eloquence elucidation elusion email embargo
embarkation embarrassment embezzlement emigration emission emotion
empathy emphasis empire employ employment empowerment emptiness
encounter encouragement encroachment encyclopedia end endeavor
ending endorsement endurance energy enforcement engagement enigma
enjoyment enlargement enlightenment enmity enormity enquiry enrollment
entanglement enterprise entertainment enthusiasm entirety entitlement
entity entrance entreaty entry enumeration environment envy epic
epidemic episode epoch epilogue equality equation equilibrium
equinox equipment equity equivalence era eradication error eruption
escape essay essence establishment estate esteem estimation ethics
etiquette eulogy evacuation evaluation evangelism evaporation eve
evening event eventide eventuality evidence evil evocation evolution
exactitude exaggeration examination example excerpt excess exchange
excitement exclamation exclusion excommunication excuse execution
exemption exercise exertion exhaustion exhibit exhibition
exhortation existence exit exodus expansion expectancy expectation
expedition expenditure expense experience experiment expertise
expiration explanation exploit exploitation exploration explosion
exponent export exposition exposure expression expulsion extension
extent exterior extinction extortion extra extravagance extreme
eye eyesight fable face facility fact factor failure faith faithfulness
fallacy fallout falsehood fame familiarity fanaticism fancy fantasy
fare farewell fate fatigue favor favorite fear feast feat feature
feedback feeling felicity fellowship ferocity fertility fervor
festival festivity feud fever fiasco fiat fiction field fight
figure file filtration final finale finance financing finding
fine finesse finish firearms firmness first fishing fit fitness
flag flair flame flap flare flash flatness flattery flavor flaw
flick flight flicker flip float flood flop flow fluctuation fluency
fluidity flurry flutter focus foe folklore folly foment food
foothold footing footprint footstep force forecast foregoing
foresight forethought foreword forfeit forgery forgetfulness
forgiveness form format formation formulation forte fortune
forum forwarding foul foundation fractal fraction fragility
fragment fragrance frailty framework franchise fraternity fraud
frenzy frequency freshness friction friendship fringe front
frontier frost frown fruition frustration fuel fulfillment fulness
function fund fundamental funding funeral fur furtherance furtiveness
fury futility future gab gag gaiety gain gait galaxy gall gallop
gambit game gamut gap garbage gathering gauge gay gaze gender
generality generation generosity genesis genius genre gentility
gesture ghost gig gift gig glance glare glee glimpse glimmer
gloom glory glow gluttony go goal godliness godsend good goodbye
goods goodwill gospel gossip grab grace gradient graduation grand
granddaughter grandeur grandson grant graphic graphics grasp
gratification gratitude gravitation gravity grease great greed
greeting grief grievance grimace grin grip gripe grit groan
grouch ground group growth grudge grumble guarantee guess guest
guidance guide guilt gulf gumption gusto guts habit habitat
hack hail halfhearted halftime hallmark halt hangover happening
happiness hard hardheaded hardship harmony harvest haste hatch
hatred haul have having havoc hazard headache headline heading
headquarters headship headway healing health heap hearing heart
heartache heartbeat heartbreak hearth heat heaven heaviness
heck hedge hedonism heed heft heir heirloom helix hello help
helpfulness hemisphere herald hereafter heresy heritage hero
heroics heroism hesitation heterogeneity heyday hi hiatus hiccup
hickup hiding hierarchy hike hilarity hindrance hindsight hint
hire history hit hoarding hobby hobo hoe hold holding holiday
home homogeneity honesty honor hope hopelessness horizon
horror hospitality hostage hostility hour housekeeping housework
hover howdy howdy hub hue hug humanism humanity humbleness
humidity humiliation humility humor hunch hung hunger hunt
hunting hurdle hurl hurrah hurry hurt husbandry hush hybrid
hygiene hype hypochondria hypocrisy hypothesis hysteria icon
ideology idea ideal idealism identification identity idiom
idiosyncrasy idleness idolatry ignition ignorance illegality
illness illumination illusion illustration image imagination
imbalance imitation immaturity immediacy immensity immersion
immigration immobility immunity impact impartiality impasse
impatience impeachment impediment imperative imperfection
imperialism impersonation impersonality impetus implementation
implication implicit import importance imposition impossibility
impotence imprecision impression imprint imprisonment improvement
improv improvisation improvidence improvisation impudence impulse
impurity inability inaccuracy inactivity inaction inadequacy
inanimate inappropriateness inattention inauguration incapacity
incarceration incentive inception incest incidence incident
incidental inclination inclusion income incompatibility
incompetence incomprehension inconsistency inconvenience
increase incredulity indecency indecision independence indication
indifference indigence indignation indignity individuality
indoctrination induction indulgence industry inefficiency
inequality inequity inertia inexperience infamy infancy infection
inference infestation infidelity infiltration infinity infirmity
inflation inflexibility influence info information infraction
infusion ingestion ingratiation ingratitude inhalation
inheritance inhibition initiation initiative injunction injury
injustice inlet innards innocence innovation inopportuneness
input inquest inquiry inroad insecurity insemination insensitivity
insight insignificance insincerity insistence inspiration
instability installation instance instant instinct instruction
insubordination insufficiency insurance insurgency insurrection
intactness intangibility integration integrity intellect
intellectualism intelligence intemperance intensity intent
intention interaction interception interconnection interdependence
interdict interest interference interim interjection intermingling
intermission internalization internment interpretation interregnum
interrelation interrogation interruption intersection interval
intervention interview intimacy intimation intimidation intolerance
introspection introversion intrusion intuition invalidation invasion
invective inventory investigation investment invitation invocation
involvement iota irrationality irreverence irritation isolation
issue itinerary jaundice jealousy jeopardy jet jibe jitters
job jockstrap join jolt jostle journey joy jubilee judgement
judgment judo juice jumble jump junction jurisdiction jurisprudence
justice justification juvenile kaleidoscope karma kibosh kid
kidnap kill killing kinase kind kindergarten kindness kinetics
kinship kismet knack knell knockout know knowhow knowledge
known labor labour lack lag land landslide language languor
lapse largesse lark lash lassitude latency late latency laterality
latitude laudation launch law laxity laying layoff lead leadership
leaflet league leak leakage leaning leap learning lease leash
leave ledger leftover legacy legalism legend legibility legion
legislation legitimacy leisure length leniency letdown letter
level leverage levitation levity lexicon liability libel
liberalism libertarianism libertinism liberty libido libretto
license lien lieu life lifeblood lifeline lifespan lifestyle
lifetime lift light lightheadedness lightness likelihood
likeness liking limbo limit limitation limo lineage linguistics
link linkage list listing literature litigation liveliness
living load loan lobbying localization locale location lockup
logic logistics loitering long look looking loom loop loophole
loose loot loss lot love lowdown loyalty lull lumbago lunacy
lunge lure lust luxury lying lyric machination machismo
macrocosm madness magic magnificence magnitude maintenance
majesty majority makeup making malady malaise malaria malfeasance
malfunction malice malnutrition malpractice mandate maneuver
manhood mania manifesto manipulation mankind manner mannerism
manners manslaughter manufacture manuscript mapping marathon
march margin marijuana marriage martyrdom marvel masculinity
masking masochism mass massacre massage match matchup materialism
materiality matrimony matter maturation maturity maxim maxim
maximization maximum may mayhem meagerness meaning meanness
means measure measurement mechanics mediation meditation medium
meekness meeting melancholy mellowness melting membership memento
memoir memorandum memory menace menopause mentality mention
mentoring menu mercantilism mercy merger merit meriting
messaging metabolism metamorphosis metaphor method methodology
meticulousness metric metrology mettle middle midnight midway
migration mildness mileage militancy militarism minimization
minimum ministry minor minority minute miracle mire mirroring
misadventure misalignment misanthropy misapprehension misappropriation
misbehavior miscalculation miscarriage mischance mischief misconception
misconduct misdemeanor misdirection misery misfeasance misfortune
misgiving mishap misinformation misinterpretation misjudgment
mismanagement misplacement misprint misreading misrule misspelling
misstatement mistake mistrial mistrust misunderstanding misuse
mite mitigation mix mixture mnemonic mobility mockery mode modeling
moderation modernization modesty modicum modification modulation
moment momentum monastery monetarism money monism monochromatism
monogamy monopoly monosyllable monotony monument mood moon moonlight
moral morale morality moratorium more mores morning morphogenesis
mortality mortification motion motivation motto mound mount mouth
movement moving much multiplicity multitude murder murmur museum
music muster mutilation mutiny mutuality myth mystery mysticism
mythology nag nailing naming nap narrative narrowness nation
nationalism native nativity nature naturism nausea naysayer
nearness neatness necessity neglect negligence negotiation
neighborhood nepotism nerd nerve nescience neurosis neutrality
neutralization newcomer newness news niceness niche nigh night
nightfall nightmare nihilism ninepin nip nirvana nitrification
nobility nod noise nominalism nomination noncompliance nonentity
nonevent nonfeasance nonpayment nonsense nook norm normality
north nostalgia notch note nothingness notice notification notion
notoriety novelty now nucleation nudge nuisance number nuptials
nutrition oath obedience object objection objective objectivity
objectivity obligation oblivion obscenity obscurity observation
obsession obsolescence obstacle obstinacy obstruction occasion
occlusion occupation occurrence odds odium offense offer offering
office officialism offshoot offspring ogle ohm oneness onset
onslaught openness opportunism opportunity opposition oppression
optimism optimization option order orderliness ordinance ore
organic organicism organization orientation origin original
originality orthodoxy ostensibility ostentation otherness outage
outbreak outburst outcome outcry outdoors outfit outgrowth outing
outlast outlaw outlay outlook outlook output outrage outreach
outset outside outskirts overabundance overachievement overactivity
overall overcome overdose overestimation overexposure overflow
overkill overlap overpowering overreach overreaction override
oversight overstatement overstep overthrow overtime overture
overturn overuse ovulation ownership pace pack pain painting
pair pallor pandemonium panic parable parade parallax parallelism
paralysis paramountcy paranoia paraphrase parenthood parity
parlance parley parody paroxysm part partial partiality
participation particularity partnership pass passage pastime
pathology patience patriotism patronage patter pause pawn pay
payback payer payment peace peacefulness peak peculiarity pedagogy
pedantry pedigree peer penalty penance pendency penetration penitence
pennant penology pensiveness pep perception perdition peril period
permanency permission permit perpetuity perplexity persecution
perseverance persistence personality personification perspective
perspicuity persuasion pertinence pessimism pestilence petition
philanthropy philosophy phobia phonetics phonology photography
phrase physicality physics physiology picket picture piece pilferage
piloting pinnacle pinpoint piracy pitch pithiness pity pivot pizazz
place placement plagiarism plan planetarium planning plaque play
playback plea plea plead pleading pleasure pledge plight plot
ploy plunge plurality pluralism ply plying poetry point poise
poke policy politics polling pollution polygamy pomposity ponder
pond pool popularity portent portion portrait position positivism
possession possibility postulate posture potency potential potentiality
poverty power practice pragmatics pragmatism praise pranayama
prank prayer pre preamble precaution precedence precedent precept
preciousness precipitation precision preclusion precociousness
precognition precondition precursor predation predestination
predicament predication prediction predilection predisposition
predominance preemption preference prefix pregame prehistory
prejudice preliminary prelude premature premiere premise
preoccupation preparation preparation preponderance presage
presence present presentation preservation presidency press
pressure prestige presumption presupposition pretense pretension
prettiness prevalence prevarication prevention preview previous
price pride primacy primary prime primness principle privacy
privilege privy prize pro proactivity probability probation
probing problem problematic procedure proceeding proceeds process
procession proclamation procurement prodigy production profanity
profession proficiency profile profiteering profusion progeny
prognosis program progress progression prohibition projection
proletarianism proliferation prolongation prominence promise
promotion prompt proneness proof propaganda propagation propensity
proposal proposition propriety prosecution prospect prosperity
prostration protection protest protocol protracting proviso
prudence psalm psychosis puberty publication publicity puff
pulmonology pulse punctuality punishment purgation purity purport
purpose pursuit push putt quagmire qualification quality quandary
quantification quantity quarantine quarrel quart quartile quasi
query quest question queue quibble quickness quiet quietness quip
quirk quiz quota quote race racism radiation rage raid rain rainbow
rainfall raising rally range rank rap rapidity rapport rapture
rashness rate rating ratio rationale rationality rationing rattle
reach reaction readability readiness reading realism reality
realization reason reasoning reassurance rebate rebellion rebound
rebuff rebuke recall recap recapture recasting receipt reception
recess recession recipe reciprocity recital recitation reckoning
reclamation recognition recoil recollection recommencement
recommendation recompense reconciliation reconstitution reconstruction
recording recourse recovery recreation recriminating recruitment
rectitude recuperation recurrence redefinition redemption redirection
reduction redundancy reefer reel reentry reference referendum refinement
reflection reflux reform refreshment refuge refusal refutation regard
regeneration regimen region registration regression regret regulation
rehabilitation rehash rehearsal reign reincarnation reinforcement
reinstatement reissue rejection rejoicing rejuvenation relapse
relationship relativity relaxation relay release relegation
relevance reliability reliance relief religion relinquishment
relish reluctance remainder remand remark remedy remembrance
reminder reminiscence remission remnant remorse removal
remuneration renaming renascence rendering rendezvous renewal
renown renunciation reoccurrence reorganization reparation
repatriation repayment repeal repetition replacement reply
report repose representation repression reprimand reprisal
reproach reproduction republication repudiation repulsion
reputation request rescission rescue research resemblance
resentment reservation residency residuum resignation resiliency
resistance resolve resolution resort resource respect respiration
response responsibility rest restitution restoration restraint
restriction result resumption resurgence resurrection retaliation
retention retirement retort retreat retribution retrieval
retrogression return reunion revamp revaluation revelation
revelry revenge revenue reversal review revision revitalization
revival revocation revolt revolution revulsion reward rhetoric
rhyme rhythm ride ridicule right rigor rigidity rigmarole rigor
ripoff ripple rise rising risk risque ritual rival rivalry rlr
road roar role romance roost rotation rote rough round roundup
rout route routine row royalty ruckus ruin rule ruling rumble
rumor run rundown runoff rupture rush saga sake salary sale
salience salvation salute salvaging sanction sanctity sanctuary
sang sanity satisfaction saturation saturation savagery savings
savvy say saying scandal scarcity scene scenery scent schedule
scheme schism scholarship schooling science scoop scope score
scorn scourge scouting scrape scrimmage scruple scrutiny search
secession second secrecy secret secularism security sedition
seduction see seeming segregation selectivity self selfhood
sellout semantics seminar semiotics sense sensibility sensitivity
sentence sentimentality sentinel separation sequel sequence
serendipity serenity service serving session setback setting
settlement severance severity shade shakedown shame sharing shortage
shortcoming shortfall showcase showdown shuffle shuffling shutdown
shutting siding sigh sight silliness simplicity simplification
simulation sin singlehood singularity site situation size skepticism
skill skittishness slander slavery sleeping slouch slowness small
smell smile smoothness smugness snap snare snobbery society sociology
soliloquy solitude solstice solvency sorrow sort soul soulfulness
sound space spacing span speaking specification spectacle speculation
speech speed spell spelling spending sphere spiel spin spirit
spirituality splendor split splurge sport spotlight spread spree
spring springtime sprinkling spurt squad squall stability stab
staging stagnation stake stalemate stamina stand standing standoff
standpoint standstill start startup state statement statesmanship
status steadfastness steadiness stealth stench step stereotype
stethoscope stewardship stigma stiffness stimulation sting stipulation
stirring stock stop stopover stoppage storage story strain
strategy stratification stress stretch stride strife strikes
string stroll strut stuff stumble stump stunt stupidity stutter
style subjection subjectivity subjugation submission submissiveness
subordination subsidy substance succession success succession
suggestion suitability sum summary summation summer sunlight sunrise
sunset superabundance superpower supervision supplement support
suppression surcharge sureness surge surmise surname surplus surprise
surrender surveillance survival suspicion sustainability swagger
swap sweat sweep swell swerve swing symbol symmetry sympathy
symptom synagogue syndrome synergy synonym synthesis system
tactics talent tale talk tally tang tangle tape taproot tardiness
target tariff task taste tattoo tax teaching tear technicality
techniques technology tediousness telephone telepathy televangelism
temerity tempo temperament temperance temperature tempest tension
tenure term termination terror test testament testimonial testimony
thanksgiving thaw theism theme theocracy theology theorem theorization
theory therapeutics therapy thesis thing thinking thirst thought
thrall thread threat thrift thrill throng throw thrust
ticklishness tidings tie tightrope till tilt time timeline
timing tinge tip tirade tiredness tithe title titter toast
toggle tolerance toll tone tonight top torment torture toss
total totality touch tour tournament toxicity tracing track tradition
tragedy trail training trait tranquillity transaction transcendence
transcript transfer transformation transgression transience
transit translation transmission transparency transportation
travel traversal travesty treachery treason treasure treatment
treaty trend trepidation trial tribute trick trifle trigger
trimming triumph triviality trouble trout truancy truce truculence
truism truth trying tuition tumult tune tunnel turmoil turn
turnaround tutelage tweet twilight twinge twist type tyranny
ubiquity ugliness uglification ultimatum umbrage uncertainty
uncle unconditional unconsciousness undercurrent understanding
undertaking unease unemployment unevenness unhappiness uniformity
union unity universality universe unkindness unpleasantness unreality
unrest unruliness unwilling upbringing upgrading upheaval uplift
uplifting upkeep upsurge uptrend urgency usage use usefulness
utility utilization vacancy vacation vacillation vagary vagueness
validation validity valor value vanity variability variance
variation variety vendetta vengeance verification veritable
verity verge vernacular verse version veto vexation viability
vibe vibration vice victimization victory view viewpoint vigil
vigor vile vindication violation violence virginity virtuality
virtue visibility vision visit vitality vitamin vivacity vocation
vogue voice void volition volume volunteerism vortex vote
voyage vulnerability wage wait wakefulness walkup wandering
wannabe want war ward warfare warning warranty wastefulness
watchfulness wave wax way wealth wear weariness weather wedding
weekday weekend weigh welfare welter wheeling whim whimper
whirl whirlwind whisper whistleblowing whit whitewash whiz whole
wholeness whoop width will willingness win wind windfall winter
wisdom wish withdrawal witness wittiness wizardry woe womanhood
wonder wont word work worker workload worksheet world worry
worship worth wound wrap wrath wreckage wrong wrongdoing wrongness
yawn yea year yearning yell yelp yes yesterday yesteryear yield
yoke youth zeal zealotry zest
""".split())


# Profanity / slurs to exclude.
PROFANITY = set("""
anus arse asshole ballsack ballsacks bastard bestiality bitch
bollocks boner boob boobs cock cocks coitus cum cunt dick dicks
dildo dyke ejaculate fag faggot fellatio fetish fisting fuck fucker
fucking genitals genitalia horny hymen incest jerk jism jizz
kike masturbate masturbation nigger nig orgasm orgy penis piss pissing
porn porno pornography prick pube pubes pussy queer rape raping rapist
retard scrotum semen sex sexed shit slut slag smut spunk sperm testicle
testicles tit tits titties turd vagina vulva wank wanker whore
""".split())


# ========== Curated supplement ==========
# Hand-picked common concrete objects that MUST be in the list no matter
# what WordNet does. Kept alphabetical by category for sanity.

CURATED_EXTRAS = set("""
abacus accordion acorn aircraft airplane airport album almond
ambulance amplifier anchor ant antenna antler anvil apartment ape apple
apricot apron aquarium arm armchair armor arrow artichoke ash ashtray
asparagus asphalt asteroid astronaut atlas attic auditorium avocado axe
backpack badge badger bagel baguette balcony ball balloon ballot ballpoint
banana bandage bandana banjo bank banner barbell barbell barn barnacle
barometer barrel bartender basement basilisk basin basket basketball
bass bassoon bat bath bathrobe bathtub battery beach beacon bead beak
bean beanbag beanie bear beard beaver bed bedroom bee beef beetle
beeper beet bell bellhop belly belt bench berry bib bicycle bidet bike
bikini bill billboard binder binoculars birch bird birdcage birdhouse
biscuit bison blackberry blackboard blade blanket blender blimp blinds
block blood blouse blowdryer blowfish blueberry boa board boat bobbin
bobcat bobsled bolt bomb bone bonfire bonsai book bookcase bookend
bookmark boomerang boot bottle bouquet boulder bow bowl bowtie box
boxer boy bra bracelet brain bread breastplate brick bridge briefcase
broccoli broom brownie brush bubble bucket buckle bud buffalo buffet
bug bugle building bull bulldog bulldozer bullet bumper bun bunny
burger burrito bus bush butter butterfly button cabbage cabin cabinet
cable cactus cafe cage cake calculator calf calendar calf camel camera
camouflage can canary candle candy cane canister cannon canoe canopy
cantaloupe canyon cap cape capsule car caramel cardboard cardigan cargo
carnation carpet carrot cart cartoon cartwheel carving cashew casket
castle cat catamaran caterpillar cathedral cauliflower cave cedar ceiling
celery cello cement centipede cereal chain chainsaw chair chalice chalk
chameleon chandelier charger chariot cheddar cheek cheese cheesecake
cheetah cherry chess chest chestnut chicken chickpea chimney chimp
chimpanzee chin china chip chipmunk chisel chocolate chopstick church
cigar cigarette cinder cinnamon circuit citrus city clamp clarinet clasp
claw clay cleaver cliff clipboard cloak clock cloth clothing cloud clove
clover clown coast coat cobra cockroach coconut cocoon coffee coin
collar color colt column comb comet compass computer cone container
cookie coral cord corduroy cork corkscrew corn cornstarch cosmos costume
cot cottage cotton couch countertop cow cowboy coyote crab cracker
cradle crane crate crater crayon cream credit crepe cricket crib
cricket crocodile croissant crop crossbow crow crown crowbar crumb
crutch crystal cub cube cucumber cuff cup cupboard cupcake curb curtain
cushion custard cutlass cutlery cylinder cymbal daffodil daisy dam
dandelion dart dashboard dasher deck decoration deer denim dentist
derrick desert desk detergent diamond diaper dice dictionary diesel
dingo dinosaur dish dishwasher disk ditch divan divan diver dock dog
doghouse doll dollar dolphin dome dominoes donkey donut door doorbell
doorknob doormat doughnut dove dragon dragonfly drain drainpipe drapery
drawbridge drawer dresser drill drink driveway drone drum dryer duck
duckling dumbbell dumbbell dumpling dumpster dune dungeon dust duster
dvd eagle ear earmuff earphone earplug earring earth earthworm easel
eclair eel egg eggplant elbow elephant elevator elf elk elm embryo
emerald emu envelope eraser escalator eucalyptus eyeball eyebrow eyelash
eyelid fabric face factory fairy falcon fan fang farmhouse faucet
feather fedora fence fender fern ferret ferry fiddle fig figurine file
filet film filter fin finch finger fingernail fireball firecracker
firefly firehose fireplace firetruck firewood fish fishhook fishpond
fist flag flagpole flame flamingo flannel flashlight flask flea fleece
flip flipper floor flowerbed flute fly foam foil foot football forceps
forehead forest fork fortress fossil fountain fox foxhound freckle
freezer freighter fridge frog frosting fruit fudge funnel fur furniture
galaxy galley gallows game gameboard garage garden gardenia gargoyle
garlic gas gasket gate gauntlet gavel gazebo gazelle gear gecko gel
gem generator geode geranium ghost giant gift gill ginger giraffe girl
gizzard glacier gland glass globe glove glue gnat gnome goat goblet
goggles gold goldfish golfball gong goose gorilla gourd gown gpu
grain grape grapefruit grass grater gravel gravy greenhouse griddle
grill grin grip groin groundhog guacamole guard guava guitar gum gun
gurney guy gym gypsum hacksaw hail hair hairbrush hairclip hairpin
hallway hamburger hammer hammock hamper hamster hand handbag handcuff
handkerchief handlebar hangar hanger hankie hardhat harmonica harness
harp harpoon harpsichord hat hatchet hawk hay haystack hazelnut head
headband headlight headphone headrest hearse heart heater hedge
hedgehog heel helicopter helm helmet hen hibiscus highway hill hip
hippo hippopotamus hive hoe holly hollyhock holster home honey honeybee
honeycomb honeysuckle hood hoof hook hoop horn hornet horse horseshoe
hose hospital hostel hotdog hotel hourglass house houseboat houseplant
hovercraft hub hubcap huckleberry hummingbird hut hyacinth hyena igloo
iguana infant ink inkpot insect instrument intestine iris iron ivory
ivy jacket jaguar jail jalapeno jam janitor jar jasmine jaw jay jeans
jeep jelly jellyfish jersey jet jewel jewelry jigsaw jockey joint
journal joystick judge juggler jug juice jukebox jumper jungle juniper
junk jury kale kangaroo kayak kettle key keyboard keychain keyhole kid
kidney kimono king kingdom kingfisher kite kitten kiwi knapsack knee
kneepad knife knight knitwear knob knocker knot koala knuckle label lace
lacquer ladder ladle ladybug lagoon lake lamb lamp lampshade lantern
lapdog laptop larva larynx laser lasso latch latex lathe lattice lava
lavender lawn lawnmower lead leaf leash leather leek leg legging legwarmer
lemon lemur lentil leopard leotard letter lettuce lever library license
lichen lid lifeboat lifejacket light lighter lighthouse lightning lily
lime limo limousine linen link lint lion lip lipstick liquid liver
lizard llama loaf loafer lobby lobster lock locker locket locomotive
log logo lollipop loom lotion lotus loudspeaker lounge luggage lumber
lung lynx lyre macaroni machine mackerel magazine magnet magnolia
magpie mail mailbox mallet manatee mandolin mane mango mangrove manhole
manicure mannequin mansion mantis mantle maple marble marigold marimba
marker marlin marmot marshmallow marsupial marzipan mask mast mat match
mattress meadow medal medallion medkit melon menorah meow mesh metal
metronome microchip microphone microscope microwave milk milkshake mill
millipede mincemeat mineral minivan mink minnow mint mirror mist mitt
mitten moat mocassin moccasin mockingbird mole mollusk monarch monitor
monkey monocle monster moon moose mop moped morsel mortar mosque moss
moth mother motherboard motorbike motorboat motorcycle mound mountain
mouse mouse mousepad mouth mud muffin muffler mug mulberry mule
murmur mushroom muskox musket mussel mustache mustard muzzle nail nameplate
napkin narwhal neck necklace necktie needle nest net netbook newel
newspaper newt nickel nightclub nightgown nightingale nightstand nipple
noodle noose nose nostril notebook notepad nozzle nugget nunchucks nut
oak oar oasis oatmeal oats obelisk oboe ocean octopus odometer office
ointment okra olive omelet onion opal opossum orange orangutan orbit
orca orchard orchid organ ornament ostrich otter ottoman outhouse outlet
oven owl oxen oxygen oyster pacifier package padlock page paint
paintbrush palace palette palm pan pancake panda pane panini pannier
panties pantry pants papaya paper paperback paperclip parachute parakeet
parasol parcel parchment parent park parka parmesan parrot parsley
parsnip parsnip partridge pasta pastry patch patio paw pawn pea peach
peacock peanut pear pearl pebble pecan pedal pegasus pelican pen
pencil pendant pendulum penguin penny pepper peppermint perfume periscope
permit persimmon pestle petal petri petunia pew phone phonograph
photo photograph piano pickaxe pickle pickup picture pie pier pig
pigeon piggybank piglet pigment pile pill pillar pillow pilot pimple
pincushion pine pineapple pipe pistachio pistol piston pit pitcher
pizza placemat plain plane planet plank plant planter plaque plaster
plastic plate plateau platform platinum platter platypus playground
plaza plier plough plow plug plum plumber plume plunger pocket pod
podium pole polecat polish pollen pomegranate pompom pond pony poodle
pool popcorn poppy porcelain porch porcupine porkchop porridge
porthole portrait possum post postcard poster pot potato pottery
pouch poultry powder prairie prawn preservative president pretzel
primrose prince princess printer prism prison probe projector pronghorn
propeller prune pudding puddle puffin pug puggle pug pulley pump
pumpkin punch puppet puppy purse pushpin puzzle pyjama pyramid python
quail quarry quart quarter quartz quasar queen quesadilla quetzal quill
quilt quinoa rabbit raccoon racetrack racquet radar radiator radio radish
raft rag railroad rain rainbow raincoat raindrop raisin rake ram ranch
raspberry rat ratchet rattle rattlesnake raven ravioli ray razor
rearview rectangle reed reef reel refrigerator reindeer rein reservoir
restaurant retina revolver rhino rhinoceros rhubarb rib ribbon rice
rickshaw rifle ring rink river road roadside roast roadwork robe robin
robot rock rocker rocket rod roe roll roller rolodex roof rook rooster
root rope rose rosebush rosemary roundabout rowboat rowhouse ruby rudder
rug rugby ruler rum rutabaga saber sack saddle safe safety sail
sailboat sailor salad salamander salami salmon salsa salt sand sandal
sandbag sandbox sandpaper sandwich sapphire sardine sari sarong sash
satellite satsuma saucepan saucer sauerkraut sausage saw sawdust saxophone
scab scabbard scaffold scale scallop scalp scalpel scanner scar scarecrow
scarf school scissors scone scoop scooter scorpion scout scraper screen
screw screwdriver scroll scrub scuba sculpture seal seashell seat seaweed
seed seedling seesaw semicolon semitruck senator sequin servant setter
shack shackle shadow shaft shake shampoo shark shawl shearling shears
shed sheep sheet shelf shell shepherd sherbet shield shin ship shirt
shoe shoelace shoo shooter shop shopkeeper shore short shortbread shorts
shoulder shovel shower shrew shrimp shrine shrub shrug shuttle shuttlecock
sibling sickle sidewalk sieve sigma silk silo silver simian sink sister
skate skateboard skeleton sketchbook ski skier skillet skin skirt skull
skunk sky skylight skyline skyscraper slab slat sled sledge sledgehammer
sleeping sleigh slide slinger slingshot slipper sloop sloth slug slurry
smith smock smog smoke smokestack smoothie snail snake snapper snare
sneaker snorkel snout snow snowball snowboard snowdrop snowflake
snowman snowmobile snowshoe soap soapbox soccer sock socket sod soda
sofa softball soil soldier sombrero son songbook soot sorbet soup spa
space spacesuit spaceship spade spaghetti spandex spark sparkler sparrow
spatula speaker spearmint spectacles speedboat spider spigot spike
spinach spine spire spitz splint splinter sponge spoon spore spout sprig
spring sprinkler sprout spruce spur spyglass squid squirrel stable
stadium stag stagecoach stairs stake stallion stamen stamp staple
stapler star starfish statue steak steamboat steamer steel stem stencil
step stereo steroid stethoscope sticker stick stiletto sting stingray
stirrup stitch stockade stocking stogie stoic stomach stone stool stop
stoplight stopwatch store stork storm stove strainer strap straw
strawberry stream street strip stripe stroller strudel stump suburb
subway sugar suit suitcase sun sundae sundial sunflower sunglasses
sunlamp sunrise sunset supermarket surfboard sushi swab swallow swamp
swan sweatband sweater sweatpants sweatshirt swimsuit swing sword
swordfish syringe syrup table tablecloth tablet taco tadpole tail
tambourine tan tangerine tank tankard tanker tap tape tapestry tapeworm
tapir tarantula target tart tassel tattoo tavern teacher teacup teakettle
teapot teddybear teeth television temple tennis tent tentacle teriyaki
terminal termite terrace terrapin terrier tesla test testtube textbook
thermometer thermos thermostat thicket thigh thimble thistle thong thorax
thorn thread throat throne throttle thumb thumbtack thunder tiara tick
ticket tie tiger tights tile timer tinsel tinder tire tissue title
toad toaster toe toenail toffee tofu toga toilet tomato tomb tongs
tongue toolbelt toolbox tooth toothbrush toothpaste toothpick top
topaz torch tornado torpedo torso tortilla tortoise totem toucan
tow towel tower town toy track tractor trailer train tram trampoline
trash trawler tray treasure tree trellis trench triangle tricycle
trifle trigger trim trolley trombone trophy trout trowel truck trumpet
trunk tshirt tsunami tub tuba tulip tuna tundra tunic tunnel turbine
turf turkey turnip turquoise turtle tusk tutu tuxedo tv tweed tweezer
twig typewriter udder ukulele umbrella uniform unicorn unicycle urchin
urn usb utensil vacuum valley valve vampire van vanilla vase vat vault
vegetable veil vein velvet vending vent ventricle venus veranda vertebra
vest vice vignette village vinegar vineyard vinyl violet violin viper
vise visor volcano volleyball voltmeter vulture waffle wagon waist
wall wallet wallpaper walnut walrus wand ward wardrobe warehouse warship
wart wasp waste watch water watercolor waterfall watermelon wave wax
web weed whale wheat wheel wheelbarrow wheelchair whetstone whip whisker
whiskey whisky whistle wick wig wigwam willow winch wind windmill window
windshield wing wire wisp wok wolf wolverine wombat wood woodpecker
wool worker workshop worm wrapper wrench wrist wristband xray yacht yak
yam yard yarn yew yoga yogurt yolk yo-yo yurt zebra zeppelin zero zipper
zoo zucchini
""".split())

# Additional common concrete nouns that my blacklist accidentally caught OR
# that the hypernym filter cuts. Adding them here guarantees inclusion AND
# overrides any blacklist entry. Keep this list tightly concrete.
CURATED_EXTRAS |= set("""
eye mouth drill tie tongue head ear nose lip hair skin neck face arm leg
hand foot knee elbow thumb wrist ankle heel chin cheek throat chest back
shoulder hip waist thigh calf forehead jaw brow heart liver lung kidney
brain bone muscle skull rib spine nerve vein artery gland thyroid pancreas
bladder intestine tonsil spleen stomach appendix gallbladder esophagus
trachea larynx pharynx sinus pupil iris cornea retina lens eardrum nostril
uvula gum tooth molar palate dimple eyelash eyebrow knuckle fingernail
toenail belly bust nipple navel pore tear sweat saliva mucus
badge base balm band body bug case cash check clip dust file flag flame
food fuel gift goal ground hedge kid letter light link list match mix
money moon nap note picture point pond pool prize rain reel shade step
string tape tip top tongue tunnel air card bone bullet bar basin basket
bed bike ball bandage block boat bolt bomb book boot bottle bow box boy
branch brick bridge bucket bud button cable cage cake can candle cap car
cat chair chain chest child chip church city clock cloth cloud club coat
coin comb cook cord cot couch court coupon cup curtain dart deck disk
dish dog doll door dress drug drum egg engine envelope fan fence film
finger fire fish floor flower fog fork fridge fruit gas gate gel glass
globe glove glue gold gown grape grass gun gym hair hand hat head heart
helmet hill hole hook horn horse hose hotel house ice ink iron island
jacket jar jewel key king knee knife knob knot lake lamp lawn leaf
leather leg lens letter lie light lime line link lion lip liver loaf
lock log man map mask mat meat metal milk mill mirror mist motor mouse
mouth mud muscle mushroom nail neck needle nest net newspaper nose oil
oven owl page pan panel paper paste path pen pencil phone piano pick
pickle picture pie pig pill pillar pin pipe plane plank plant plate plum
pocket pole pond pool popcorn post pot powder print purse queen rabbit
radio rail record ring robe rock rod roll room rope rose rug ruler sack
salt sand saw scarf school scissors screen screw seal seat seed shade
sheep shelf shell shield shirt shoe shop shorts sign silk skin sleeve
slipper smoke snake snow soap sock soup spade spider spoon spray star
steak stem stick stone store string sugar suit sun table tail tank tape
tea teeth tent tile tin tire toe tomato tool tooth towel tower toy trap
tray tree truck tube tunnel umbrella vase veil wall watch water well
wheel whip wig wine wire wool yarn zipper
spark spout spring sprout staff stain stake stair stall stamp stand
staple statue steam steel stem step stern stew stick stile stilt stilts
sting stirrup stitch stocking stool stoop stopper stork story stove
stovepipe strap straw strawberry street strip stripe stroller stucco
stud studio study stump suitcase summer sweater sweep sword swan
saddle safari sage sail salad salon salve samurai sandal sandbag
sandcastle sandpaper sapling sardonyx sari sarong sash saucer sauna
sawfish sawhorse scab scabbard scaffold scalp scampi scaler scalpel
scanner scar scarecrow scepter schlock schnauzer schnitzel schooner
scooter score scoop scooter scorpion scotch scotty screwdriver scripture
scroll scrub scuba scull scythe sedan sentry serpent servant setter
sextant shack shackle shaft shake shampoo shark shawl shears sheath
shed sheikh shepherd sheriff sherry shingle shipwreck shirt shop shorts
shovel shrimp shrine shroud shrub shuffle shutter shuttle sickle
sieve sifter silage silk silo silver sink siren sister skateboard
skeleton skewer ski skiff skillet skunk slacks sled sledge sleet
slice slide sling slipcover slippers sloth slum smith smock snifter
snow snowball snowflake snowman soapstone sofa softener soil solder
soup spaceship spaghetti spear spectacle spectacles spell spew spile
spinach spindle spinnaker spire sponge spool spoor spore sporran
spring sprinkler spud spur squab squadron squash squid squirrel
stable stag stage stagecoach stair staircase stake stallion stamen
stamp stance staple star starboard starling station statue steed
steer stein stela stele stencil stepladder steppe stereo stew
stethoscope stew stigma stiletto stilt stilts stinger stink stirrup
stitchery stoat stockade stocking stockyard stole stomacher stone stones
stool stoop stopper storm stove stovepipe strainer strait strap
straw street stretcher string stroller studio sturgeon stylus sub
submarine submersible subway sulfur suit sulfurous sulky summerhouse
sunburn sundeck sundial sundress sunflower sungown sunglasses sunhat
sunlamp sunshade superego supplement surcoat surfboard surrey sushi
suspender swallow swamp swan swab swag sweat sweater sweats swell
swordsman swordfish sycamore syringe tabernacle tablet tack tadpole
taffeta taffy tagalong tailcoat tailgate tails tallyho tam tambour
tambourine tan tandem tangerine tanger tanker tankard tapioca tapir
tarantula target tarmac tart tarpaulin tartan tassel tavern teacup
teakettle teapot tearoom teasel teddy teepee telescope telex tern
terrace terracotta terrarium terrier tesla tessera teston testicle
textile thalamus thatch thermal thermocouple thermos thermostat thigh
thimble thinner thistle thong thornbush thread thresher throne
thumbscrew thumbtack thunderbolt thurible thymus tiara ticket tick
tidewater tie tiger tights timber timbrel tinder tinderbox tinfoil tinsel
tinsmith tipi tire tissue toad toaster toboggan tobogganist tofu toga
toggle tollbooth tombstone tomcat tomtom toolshed topee topiary
topknot topknot torch torpedo tortellini tortoise totem totem tourmaline
towel township tract tractor trailer train trampoline tramway transom
transport trash trawler treadmill treacle treat trellis trenchcoat
trestle tricycle trike trinket trireme trombone trophy trough trout
trouser trowel truck truffle trumpet trunks tsunami tub tuba tucker
tugboat tulip tuna tuner turban turbine turbofan turbojet turkey
turtleneck tusk tuxedo tweed twine typewriter ugli ukulele
ulster ulcer umbrella undercarriage underclothes underpants undershirt
undertow unguent urinal urn utility utricle vaccine vacuole vacuum
valance valise vanity vaporizer varnish vault veal vegetation vehicle
vellum velour velvet ventilator veranda vertebra vessel vestment vial
video videotape villa vinegar violin viper virus visor vitamin vodka
voile volcano vulture waders waffle wagon waistcoat walk walker walkman
walkway wallboard wallpaper walnut walrus wand warehouse washbasin
washbowl washcloth washer washstand wastebasket wastewater watchband
watchdog watchtower waterbed waterfall waterfowl watermark
watershed watervessel watercraft wax waybill weasel weathercock web
wedge wetland wheatcake whelk whey whip whirligig whisker whisk whistle
whistles whistle whitewall wickerwork wicker widescreen wifi windbag
windbreak windbreaker windjammer windmill window windowframe windowpane
windpipe windshield windsock winnower wisp wishbone withe wok wombat
wonton woodcut woodgrain woodpecker woodshed woodwork wool woolen
word workbench workshop wormwood wort wrap wrapper wrapping wreath
wrench wrestler wristband wristwatch xylophone yam yarmulke yawl yearling
yoke yolk yurt zebra zeppelin zero zipper zither zoo zucchini
""".split())


# ========== Existing list loading (for commonness filter) ==========

def load_existing_expanded(path='words.js'):
    try:
        with open(path) as f:
            content = f.read()
        m = re.search(r'const WORD_LIST_EXPANDED = (\[[\s\S]*?\]);', content)
        if m:
            return set(w.lower() for w in json.loads(m.group(1)))
    except Exception as e:
        print(f'Warning: could not load existing expanded list: {e}', file=sys.stderr)
    return set()


# ========== Main generation ==========

def get_all_noun_candidates(min_len=3, max_len=18):
    candidates = set()
    for synset in wn.all_synsets(pos=wn.NOUN):
        for lemma in synset.lemmas():
            w = lemma.name()
            if '_' in w or '-' in w or "'" in w or '.' in w:
                continue
            w = w.lower()
            if not w.isalpha():
                continue
            if not (min_len <= len(w) <= max_len):
                continue
            candidates.add(w)
    return candidates


ABSTRACT_SUFFIXES_STRICT = (
    'ism', 'ation', 'ization', 'isation', 'tion', 'sion', 'ment',
    'ness', 'ship', 'hood', 'dom', 'ity', 'cy', 'ance', 'ence',
    'ery', 'logy', 'graphy', 'phobia', 'mania',
)
# Words with these endings that ARE concrete objects; keep them.
CONCRETE_EXCEPTIONS = set("""
aberration abolition absorption accretion acidification activation
alkalation ambulation ammunition angioplasty application arbitration
archery artillery aviation aviary bakery balcony bastion battery
beachery begonia belladonna blockchain bludgeon boundary brewery
brioche buggery bulimia buoy butchery camellia camphor camphor
cannery canton canyon carpentry castration castigation cavalry
cemetery chancery chapel chrysanthemum churchyard colossus confection
conservatory construction constellation contraption cornucopia creation
creek crematorium delicatessen denomination depot dictation direction
diction distillery dormitory effigy elation embryo emporium
embankment emission encyclopedia equation eruption escalation
evolution exhibition explosion extension fabrication fiction fixation
flammation forestation fortification fortress foundry fountain fraction
gallery garrison granary gymnasium hospitalization immersion incubator
infant infection inflection infraction innovation inoculation insertion
insulation intersection intrusion invention invocation irradiation
junction lactation lakery lavatory legation liberation library lineation
location locomotion lotion magnification mansion mastication medication
medicine meditation menstruation migration mimicry ministration mission
molasses molecule monkey mosaic mummification mutation nation
negotiation neighbor nomenclature nomination notation notification
observation orchestra organization ornament ozonation palpitation
pantry parchment parry partition patisserie pavilion perambulator
perfection perforation perfusion permutation perpendicular pigmentation
planetarium plantation platoon pollination pommel population portion
possession poultry precipitation prescription preservation presentation
prism prison procession production projection promenade pronoun
publication pulsation pumpkin radiation ranch rarefaction ration
reaction realization refraction refrigeration registration regulation
remediation reprobation resurrection rifle rotation sanctuary sanitation
satiation satisfaction saturation scansion scripture secretion section
sedation sedimentation segmentation separation septum serration
session shrubbery signboard skillet solidification solution spectation
station stationery sterilization stimulation stratification striation
stud substation suffocation suggestion suppository suspension sustainer
tabernacle tenement termination tinction transaction transformation
translation transmission transportation trepidation truncheon tuition
ulceration undulation vaccination variation ventilation vermillion
vibration vicinity violation wandery warehouse zonation
""".split())


def has_adjective_senses(word):
    """True if word has adjective senses in WordNet."""
    return bool(wn.synsets(word, pos=wn.ADJ)) or bool(wn.synsets(word, pos=wn.ADJ_SAT))


def is_proper_noun(word):
    """True if ALL noun synsets of word are proper-noun instances."""
    synsets = wn.synsets(word, pos=wn.NOUN)
    if not synsets:
        return False
    return all(s.instance_hypernyms() for s in synsets)


def synset_is_concrete(s):
    hyps = get_all_hypernyms(s)
    return bool(hyps & CONCRETE_ROOTS)


def synset_is_abstract(s):
    hyps = get_all_hypernyms(s)
    return bool(hyps & ABSTRACT_ROOTS) and not bool(hyps & CONCRETE_ROOTS)


def word_is_concrete(word):
    """
    Strict concrete-noun test:
      1. Must have noun senses.
      2. PRIMARY sense (synset[0]) must be concrete and NOT an instance.
         This alone kills "address" (computer code), "absorption" (process),
         "adam" (person instance), "alabama" (state instance), "action",
         "activity", "access", "niche" (primary sense "status"), "sin"
         (primary sense "transgression"), etc.
      3. Word must not be primarily an adjective.
      4. Word must not be a nationality/ethnic descriptor.
    """
    synsets = wn.synsets(word, pos=wn.NOUN)
    if not synsets:
        return False

    primary = synsets[0]

    # Reject proper-noun instances (Adam, Alabama, Amazon, Dante, ...).
    if primary.instance_hypernyms():
        return False

    # Primary sense must be concrete.
    if not synset_is_concrete(primary):
        return False

    # Primary sense must not be under abstract roots.
    if synset_is_abstract(primary):
        return False

    # Reject primary nationalities / ethnic groups / languages. Examples:
    # "african", "afghan" (the person, not the blanket), "albanian",
    # "abkhas", "abkhasian" (ethnic + language). Check structural markers.
    demonym_roots = {
        'national.n.01', 'inhabitant.n.01', 'native.n.03',
        'ethnic_group.n.01', 'race.n.02',
        'natural_language.n.01', 'language.n.01',
    }
    primary_hyps = get_all_hypernyms(primary)
    if primary_hyps & demonym_roots:
        if word not in CURATED_EXTRAS:
            return False
    # Definition-based demonym check — "native or inhabitant of ..."
    defn = primary.definition().lower()
    demonym_phrases = (
        'native or inhabitant of', 'a member of', 'member of a',
        'a resident of', 'inhabitant of',
        'the language of', 'the language spoken', 'a dialect of',
    )
    if any(p in defn for p in demonym_phrases) and word not in CURATED_EXTRAS:
        return False

    # Reject if the word has ANY adjective/adverb senses but only ONE noun
    # sense — usually means we're grabbing a weak nominalized adjective.
    # Exceptions: CURATED_EXTRAS always keep.
    if word not in CURATED_EXTRAS:
        adj_syns = wn.synsets(word, pos=wn.ADJ) + wn.synsets(word, pos=wn.ADJ_SAT)
        if len(synsets) <= 1 and len(adj_syns) >= 1:
            return False

    # Suffix filter: abstract-looking endings get the axe unless whitelisted.
    if len(word) >= 6 and word.endswith(ABSTRACT_SUFFIXES_STRICT):
        if word not in CONCRETE_EXCEPTIONS and word not in CURATED_EXTRAS:
            return False

    return True


def main():
    print('Loading corpora for commonness filter...')
    corpus_words = set()
    for corp_name, corp in [('brown', brown), ('gutenberg', gutenberg),
                            ('reuters', reuters), ('webtext', webtext),
                            ('movie_reviews', movie_reviews)]:
        n = 0
        for w in corp.words():
            if w.isalpha():
                corpus_words.add(w.lower())
                n += 1
        print(f'  {corp_name}: {n} tokens; running unique total {len(corpus_words)}')
    brown_words = corpus_words

    print('Loading existing expanded word list...')
    existing = load_existing_expanded('words.js')
    print(f'  Existing WORD_LIST_EXPANDED has {len(existing)} words.')

    # Load FullDictionary.txt as a permissive "real word" gate. This lets us
    # include obscure-but-real concrete nouns (e.g. "albatross", "aardwolf")
    # that don't happen to appear in any corpus.
    fulldict = set()
    try:
        with open('FullDictionary.txt') as f:
            for line in f:
                w = line.strip().lower()
                if w.isalpha() and 3 <= len(w) <= 18:
                    fulldict.add(w)
        print(f'  FullDictionary.txt: {len(fulldict)} words.')
    except Exception as e:
        print(f'  FullDictionary.txt: failed ({e})')

    print('Pulling noun candidates from WordNet...')
    candidates = get_all_noun_candidates()
    print(f'  {len(candidates)} single-word nouns in WordNet (len 2-18).')

    print('Classifying concreteness...')
    concrete = set()
    for i, w in enumerate(sorted(candidates)):
        if (i + 1) % 5000 == 0:
            print(f'  processed {i+1}/{len(candidates)}')
        if word_is_concrete(w):
            concrete.add(w)
    print(f'  {len(concrete)} passed the concreteness test.')

    # Commonness gate. A word is accepted if ANY of these hold:
    #   A. It appears in a real-text corpus (Brown, Gutenberg, Reuters,
    #      Webtext, or Movie Reviews) — proof it's used in real writing.
    #   B. It appears in the existing curated WORD_LIST_EXPANDED — we
    #      already treat those as "common enough."
    #   C. It's in our CURATED_EXTRAS hand-picked list.
    #   D. It's in FullDictionary.txt (so it's a real English spelling)
    #      AND WordNet has ≥ 2 noun synsets for it (polysemy is a strong
    #      signal of being a real, commonly-used English noun).
    #   E. It's in FullDictionary.txt AND a WordNet lemma for this word
    #      has count > 0 (appears in tagged text).
    # This keeps real concrete nouns like "goalpost", "rollerblade",
    # "waterfowl" while dropping obscure taxonomic/brand-name junk.
    common_a = brown_words | existing | CURATED_EXTRAS
    print(f'  Tier-A corpus words: {len(common_a)}')

    def has_tagged_lemma(w):
        for s in wn.synsets(w, pos=wn.NOUN):
            for l in s.lemmas():
                if l.count() > 0:
                    return True
        return False

    def passes_commonness(w):
        if w in common_a:
            return True
        if w in fulldict:
            syns = wn.synsets(w, pos=wn.NOUN)
            if len(syns) >= 2:
                return True
            if has_tagged_lemma(w):
                return True
        return False

    filtered = set()
    for w in concrete:
        if passes_commonness(w):
            filtered.add(w)
    print(f'  After commonness filter: {len(filtered)}.')

    # Always-include: curated extras no matter what.
    filtered |= CURATED_EXTRAS

    # Always-exclude: blacklist and profanity. But NEVER remove words that
    # are explicitly in CURATED_EXTRAS (curated wins over blacklist).
    before = len(filtered)
    effective_blacklist = (ABSTRACT_BLACKLIST | PROFANITY) - CURATED_EXTRAS
    filtered -= effective_blacklist
    print(f'  Removed {before - len(filtered)} blacklisted/profane words.')

    # Sanity: only lowercase alphabetic, length in range.
    filtered = {w for w in filtered if w.isalpha() and 2 <= len(w) <= 18}

    final = sorted(filtered)
    print(f'\nFINAL: {len(final)} concrete nouns')
    print('Sample:', ', '.join(final[:30]))

    # Write plain-text list for review.
    with open('concrete_nouns.txt', 'w') as f:
        f.write('\n'.join(final))
    print('Wrote concrete_nouns.txt')

    # Write JSON for the index builder to consume.
    with open('concrete_nouns.json', 'w') as f:
        json.dump(final, f)
    print('Wrote concrete_nouns.json')


if __name__ == '__main__':
    main()
