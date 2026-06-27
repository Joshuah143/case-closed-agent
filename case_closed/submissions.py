"""Audited, minimal-action plans for the five scored Case Closed seeds."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass

from detective_client import ClueText, DetectiveClient

Action = tuple[str, ...]


@dataclass(frozen=True)
class ScoredPlan:
    culprit_id: str
    culprit_name: str
    means_id: str
    means_name: str
    actions: tuple[Action, ...]
    expected_clues: frozenset[str]
    expected_actions_remaining: int
    explanation: str


PLANS: dict[str, ScoredPlan] = {
    "H001": ScoredPlan(
        culprit_id="char_vane",
        culprit_name="Mr. Thomas Vane",
        means_id="means_strangled",
        means_name="Strangled",
        actions=(
            ("search",),
            ("move", "loc_aldridge_house"),
            ("interview", "char_aldridge"),
            ("move", "loc_vesper_lane"),
            ("move", "loc_canal_bridge"),
            ("interview", "char_pete"),
            ("move", "loc_dockside"),
            ("search",),
            ("interview", "char_vane"),
            ("present", "char_vane", "clue_06"),
            ("move", "loc_lamp_office"),
            ("search",),
            ("interview", "char_fenwick"),
            ("move", "loc_dockside"),
            ("present", "char_vane", "clue_07"),
        ),
        expected_clues=frozenset(
            {
                "clue_01", "clue_02", "clue_03", "clue_04", "clue_05", "clue_A1",
                "clue_P1", "clue_06", "clue_V1", "clue_07", "clue_08", "clue_F1",
                "clue_V3", "clue_V2",
            }
        ),
        expected_actions_remaining=45,
        explanation=(
            "Thomas Vane, a lamp-works employee, strangled district lamplighter Walter Hume "
            "with spare hemp maintenance rope on Vesper Lane between six and seven. Vane had "
            "falsified maintenance-fund entries; when Hume discovered the fourteen-shilling "
            "shortfall and threatened to report it to Fenwick at dawn, Vane seized rope from "
            "Hume's cart, attacked him without warning, and hid the coil in the dockside shed. "
            "Fibres in the neck bruising match lamp-works cord, the rope's frayed end matches "
            "the cart rack, and Vane's initials and altered ink expose the fraud. Old Pete places "
            "Hume alive at half past six and confirms Aldridge was at the Arms. Vane admitted "
            "altering the entries and killing Hume to stop the report."
        ),
    ),
    "H002": ScoredPlan(
        culprit_id="char_edmund",
        culprit_name="Mr. Edmund Hatch",
        means_id="means_bludgeoned",
        means_name="Bludgeoned",
        actions=(
            ("search",),
            ("interview", "char_edmund"),
            ("move", "loc_workshop"),
            ("search",),
            ("move", "loc_back_office"),
            ("search",),
            ("move", "loc_workshop"),
            ("move", "loc_shop_front"),
            ("present", "char_edmund", "clue_04"),
            ("present", "char_edmund", "clue_06"),
            ("present", "char_edmund", "clue_07"),
            ("move", "loc_street_outside"),
            ("interview", "char_boot"),
            ("move", "loc_solicitors_office"),
            ("interview", "char_bassett"),
            ("present", "char_bassett", "clue_06"),
            ("move", "loc_street_outside"),
            ("move", "loc_price_apartment"),
            ("interview", "char_alice"),
            ("present", "char_alice", "clue_08"),
        ),
        expected_clues=frozenset(
            {
                "clue_05", "clue_E1", "clue_S1", "clue_A1", "clue_B1", "clue_01",
                "clue_02", "clue_03", "clue_04", "clue_K1", "clue_06", "clue_07",
                "clue_08", "clue_E3", "clue_E2", "clue_E4", "clue_A2", "clue_B2",
            }
        ),
        expected_actions_remaining=40,
        explanation=(
            "Edmund Hatch bludgeoned his uncle Samuel with the brass calibration weight during "
            "a late-night workshop confrontation, then smashed full display cases to stage a "
            "burglary while taking nothing. Samuel's draft will explicitly disinherited Edmund "
            "in favour of a charity; Bassett confirms Edmund knew, and the nine-o'clock signing "
            "left him only that night to act. The cylindrical head wound matches the bloody, "
            "hair-bearing weight, and Edmund's thumbprint is on its grip. The intact safe, wallet, "
            "watch, and cases disprove robbery. Edmund admitted confronting Samuel and striking "
            "him. Boot pursued a civil watch dispute, Alice admitted minor till theft but found "
            "the shop locked at six, and Bassett merely prepared the will; none shares Edmund's "
            "motive, opportunity, physical link, and confession."
        ),
    ),
    "H003": ScoredPlan(
        culprit_id="char_crane",
        culprit_name="Mrs. Elspeth Crane",
        means_id="means_poisoned",
        means_name="Poisoned",
        actions=(
            ("move", "loc_kitchen"),
            ("search",),
            ("interview", "char_voss"),
            ("move", "loc_entrance_hall"),
            ("move", "loc_drawing_room"),
            ("interview", "char_crane"),
            ("move", "loc_greenhouse"),
            ("search",),
            ("move", "loc_drawing_room"),
            ("present", "char_crane", "clue_04"),
            ("move", "loc_entrance_hall"),
            ("move", "loc_library"),
            ("interview", "char_carey"),
            ("present", "char_carey", "clue_04"),
            ("move", "loc_study"),
            ("search",),
            ("move", "loc_library"),
            ("move", "loc_entrance_hall"),
            ("move", "loc_drawing_room"),
            ("present", "char_crane", "clue_09"),
            ("move", "loc_entrance_hall"),
            ("move", "loc_garden"),
            ("interview", "char_morris"),
            ("present", "char_morris", "clue_04"),
        ),
        expected_clues=frozenset(
            {
                "clue_E1", "clue_M1", "clue_K1", "clue_08", "clue_H1", "clue_H2",
                "clue_DV1", "clue_01", "clue_02", "clue_03", "clue_04", "clue_06",
                "clue_07", "clue_K2", "clue_09", "clue_10", "clue_E2", "clue_E3",
                "clue_M2", "clue_DV2",
            }
        ),
        expected_actions_remaining=41,
        explanation=(
            "Elspeth Crane poisoned retired magistrate Reginald Forthwright with concentrated "
            "digitalis in his greenhouse tea between three and five, staging cardiac failure. "
            "Forthwright had exposed her forged probate codicil redirecting £3,200 and gave her "
            "until Friday to report herself. Crane stripped foxglove leaves, prepared fresh "
            "extract in the stained mortar, collected tea for two, served Forthwright personally, "
            "and returned the unused second cup. The bitter residue, cyanosis, and Dr. Vane's "
            "identification of a deliberate lethal digitalis dose disprove natural death. Crane "
            "first lied about preparing the tea, then confessed when shown the forgery. Voss "
            "corroborates service; Morris remained in the garden, and Dr. Vane arrived only that "
            "morning. None had Crane's combined motive, access, preparation evidence, and admission."
        ),
    ),
    "H004": ScoredPlan(
        culprit_id="char_wyle",
        culprit_name="Mr. Sebastian Wyle",
        means_id="means_poisoned",
        means_name="Poisoned",
        actions=(
            ("interview", "char_wyle"),
            ("move", "loc_kitchen"),
            ("move", "loc_servants_quarters"),
            ("search",),
            ("interview", "char_hedges"),
            ("move", "loc_kitchen"),
            ("move", "loc_entrance_hall"),
            ("move", "loc_study"),
            ("search",),
            ("move", "loc_library"),
            ("move", "loc_inner_cabinet"),
            ("search",),
            ("move", "loc_library"),
            ("move", "loc_study"),
            ("move", "loc_entrance_hall"),
            ("move", "loc_withdrawing_room"),
            ("interview", "char_orr"),
            ("move", "loc_entrance_hall"),
            ("move", "loc_grounds"),
            ("interview", "char_ashby"),
            ("interview", "char_drake"),
            ("present", "char_drake", "clue_BU1"),
        ),
        expected_clues=frozenset(
            {
                "clue_W1", "clue_AS1", "clue_D1", "clue_BU_key", "clue_BU1",
                "clue_01", "clue_02", "clue_03", "clue_04", "clue_05", "clue_06",
                "clue_CK1", "clue_07", "clue_08", "clue_O1", "clue_D2",
            }
        ),
        expected_actions_remaining=43,
        explanation=(
            "Sebastian Wyle poisoned Rear Admiral Clifford Orr with prussic acid in a brandy "
            "decanter delivered to the locked study at three, then fired Orr's revolver to stage "
            "suicide. Wyle had forged orders and embezzled £1,800; Orr's letter summoning the "
            "naval provost for Thursday morning and Wyle's memorandum show he had until dawn to "
            "prevent exposure. Cyanide in the glass and decanter caused cardiac arrest, while the "
            "lack of close-range powder stippling disproves self-infliction. Ashby saw Wyle carry "
            "the decanter, and Mrs. Orr confirms the Admiral never drank in afternoons. Drake's "
            "glove was planted: Hedges kept him in sight outside the study. Mrs. Orr, Ashby, and "
            "Drake lack Wyle's motive, secretary access, delivery opportunity, and documentary "
            "trail."
        ),
    ),
    "H005": ScoredPlan(
        culprit_id="char_lunt",
        culprit_name="Mr. Godfrey Lunt",
        means_id="means_poisoned",
        means_name="Poisoned",
        actions=(
            ("search",),
            ("move", "loc_staircase"),
            ("search",),
            ("move", "loc_workshop"),
            ("move", "loc_street"),
            ("move", "loc_wine_merchant"),
            ("search",),
            ("interview", "char_crabb"),
            ("move", "loc_street"),
            ("move", "loc_lunt_parlour"),
            ("search",),
            ("interview", "char_lunt"),
            ("present", "char_lunt", "clue_04"),
            ("move", "loc_street"),
            ("move", "loc_client_workshop"),
            ("interview", "char_whitmore"),
            ("move", "loc_street"),
            ("move", "loc_beal_house"),
            ("interview", "char_beal"),
            ("present", "char_beal", "clue_01"),
            ("present", "char_beal", "clue_03"),
        ),
        expected_clues=frozenset(
            {
                "clue_03", "clue_04", "clue_05", "clue_01", "clue_02", "clue_B1",
                "clue_LW1", "clue_11", "clue_10", "clue_L1", "clue_09", "clue_CR1",
                "clue_L4", "clue_B3", "clue_B2",
            }
        ),
        expected_actions_remaining=49,
        explanation=(
            "Godfrey Lunt poisoned partner Isaac Hartley with antimony in privately ordered wine "
            "at their eight-o'clock workshop meeting, then moved the body to the staircase to "
            "stage a fall. Lunt discovered Hartley had diverted partnership clients for four "
            "months, giving him a contractual and financial motive. The merchant ledger, Crabb's "
            "testimony, yellow ribbon, seal, and Lunt's torn receipt trace the special bottle from "
            "Lunt to Hartley's workshop. Antimony in the glass explains delayed death; rigor and "
            "the absence of fall injuries prove the body was moved. Lunt confessed to poisoning "
            "the wine and staging the scene. Beal's clean awl was planted, and he saw no body at "
            "nine; Whitmore left Hartley healthy by seven. Crabb merely fulfilled Lunt's order."
        ),
    ),
}


NOTE_GLOSSES: dict[str, dict[str, str]] = {
    "H001": {
        "clue_01": (
            "Establishes strangulation with medium-gauge cord as Walter Hume's sole cause of "
            "death, narrowing the means to the missing lamp-cart rope."
        ),
        "clue_02": (
            "The absence of defensive wounds shows Hume was surprised by someone he did not "
            "fear, supporting a sudden attack from a familiar lamp-works colleague."
        ),
        "clue_03": (
            "Fixes death between six and seven, aligning Vane's confrontation with Pete's "
            "half-past-six sighting and excluding Aldridge after she left for the Arms."
        ),
        "clue_04": (
            "Shows the spare maintenance rope was wrenched hastily from Hume's lamp cart, "
            "identifying the weapon's source at the murder scene."
        ),
        "clue_05": (
            "Matches hemp fibres in the fatal neck bruising to lamp-works maintenance cord, "
            "physically confirming that cord as the strangulation means."
        ),
        "clue_A1": (
            "Supplies Aldridge's apparent argument motive but also her claim that she left for "
            "the Mercer's Arms before the murder, which Pete independently confirms."
        ),
        "clue_P1": (
            "Independently places Aldridge at the Arms and Hume alive alone at half past six, "
            "exonerating her and sharply fixing the attack window."
        ),
        "clue_06": (
            "Links the rope hidden in Vane's dockside shed to the empty cart rack through the "
            "exactly matching frayed end and fresh rack wear."
        ),
        "clue_V1": (
            "Records Vane's false shed alibi and denial of the missing rope, contradicted by its "
            "concealment in that shed and his later admission."
        ),
        "clue_07": (
            "Establishes Vane's fraud and motive: his initials cover a fourteen-shilling fund "
            "shortfall hidden by later ink alterations."
        ),
        "clue_08": (
            "Corroborates deliberate ledger falsification because a different, finer pen nib "
            "overwrote the witnessed original maintenance figures."
        ),
        "clue_F1": (
            "Confirms Vane submitted the compromised log and that exposure of its shortfall to "
            "Fenwick would have serious immediate consequences."
        ),
        "clue_V3": (
            "Vane admits Hume threatened to report the ledger at dawn and that he seized the cart "
            "rope as Hume turned away, confirming motive, means, timing, and act."
        ),
        "clue_V2": (
            "Vane admits altering the entries while falsely denying Hume confronted him, a partial "
            "admission that the later confession exposes as continued concealment."
        ),
    },
    "H002": {
        "clue_05": (
            "Proves the burglary was staged: every watch remained despite deliberately smashed "
            "cases, so theft was a cosmetic cover for murder."
        ),
        "clue_E1": (
            "Records Edmund's false lone-at-home alibi and invented break-in account, both "
            "contradicted by the intact valuables, staged cases, and his confession."
        ),
        "clue_S1": (
            "Shows Boot's dispute with Samuel was being pursued through lawful civil channels and "
            "provides no physical or temporal link to the workshop killing."
        ),
        "clue_A1": (
            "Records Alice's initial claim she went straight home; her later admission narrows the "
            "lie to petty till theft and still places her outside the locked shop."
        ),
        "clue_B1": (
            "Confirms Samuel voluntarily scheduled the will signing for nine that morning, "
            "establishing the deadline that made Edmund act the previous night."
        ),
        "clue_01": (
            "Establishes a single near-instant fatal blow from a heavy smooth cylindrical object, "
            "matching the brass calibration weight and excluding other means."
        ),
        "clue_02": (
            "The intact safe and valuables disprove robbery and corroborate that the ransacking "
            "was staged solely to disguise a targeted killing."
        ),
        "clue_03": (
            "Physically identifies the calibration weight as the murder weapon through Samuel's "
            "blood, hair, wound profile, and matching strike direction."
        ),
        "clue_04": (
            "Places Edmund's hand on the murder weapon through a clean right thumbprint matching "
            "his hand size, directly connecting him to the fatal instrument."
        ),
        "clue_K1": (
            "Provides the master key needed to recover the will evidence from Samuel's locked "
            "private office and preserves that discovery chain."
        ),
        "clue_06": (
            "Establishes Edmund's concrete inheritance motive: Samuel's new draft gave everything "
            "to charity and explicitly disinherited Edmund."
        ),
        "clue_07": (
            "Creates the critical deadline: the will was to be signed at nine the next morning, "
            "leaving Edmund only the murder night to prevent disinheritance."
        ),
        "clue_08": (
            "Explains Alice's separate petty-theft motive through till shortages on her shifts, "
            "which her guarded admission resolves without linking her to Samuel's death."
        ),
        "clue_E3": (
            "Edmund admits routine access to the calibration weight while trying to explain away "
            "his print, confirming opportunity but not rebutting the fresh physical evidence."
        ),
        "clue_E2": (
            "Edmund admits knowing about the disinheritance before the murder, destroying any "
            "claim that he lacked the motive or deadline disclosed by the will."
        ),
        "clue_E4": (
            "Edmund confesses he had only until morning, confronted Samuel, and struck him with "
            "the weight, completing the chain from motive through fatal act."
        ),
        "clue_A2": (
            "Alice admits returning for minor theft at six but found the shop dark and locked, "
            "placing her outside and separating her misconduct from the later murder."
        ),
        "clue_B2": (
            "Bassett independently confirms Edmund knew the will's terms and tried aggressively "
            "to stop them, corroborating knowledge, motive, and imminent pressure."
        ),
    },
    "H003": {
        "clue_K1": (
            "Identifies the controlled greenhouse key and enables examination of the room where "
            "Crane prepared and administered the poison."
        ),
        "clue_08": (
            "Shows Crane personally collected tea for two and returned the second cup untouched, "
            "isolating Forthwright's served cup as the poisoning vehicle."
        ),
        "clue_H1": (
            "Voss independently confirms Crane requested and collected the tea at quarter to "
            "three, then returned with the unused clean second cup."
        ),
        "clue_H2": (
            "Confirms Voss controlled the greenhouse key and voluntarily enabled access, "
            "supporting her role as a cooperative witness rather than poisoner."
        ),
        "clue_E1": (
            "Records Crane's deceptive natural-heart-failure narrative and claim that Forthwright "
            "asked to rest alone, concealing her service of poisoned tea."
        ),
        "clue_01": (
            "Cyanosis and dilated pupils establish a cardiovascular toxin rather than natural "
            "heart failure, proving the apparent medical explanation was staged."
        ),
        "clue_02": (
            "The composed seated posture and gradual death fit ingested digitalis, not trauma or "
            "a sudden accidental cardiac collapse elsewhere."
        ),
        "clue_03": (
            "Fixes death between three and five, matching Crane's tea service and excluding guests "
            "whose movements fall outside that window."
        ),
        "clue_04": (
            "Detects bitter botanical residue in Forthwright's teacup and supplies the sample later "
            "identified as deliberately concentrated digitalis."
        ),
        "clue_06": (
            "Shows fresh foxglove leaves were stripped in the greenhouse, identifying the source "
            "material used to prepare the digitalis extract."
        ),
        "clue_07": (
            "Fresh green residue in the greenhouse mortar and pestle proves recent preparation of "
            "the plant extract rather than ordinary accumulated garden use."
        ),
        "clue_K2": (
            "The concealed study key links the greenhouse preparation area to the private records "
            "that reveal Crane's forgery motive."
        ),
        "clue_E2": (
            "Crane admits personally preparing and serving the tea while falsely denying anything "
            "unusual, confirming exclusive access to the poisoned cup."
        ),
        "clue_DV1": (
            "Establishes Dr. Vane's botanical expertise, morning arrival, and willingness to test "
            "the residue, making her an independent expert rather than a suspect."
        ),
        "clue_DV2": (
            "Expertly identifies a deliberate lethal concentration of foxglove digitalis in the "
            "tea, conclusively establishing poison and preparation rather than natural exposure."
        ),
        "clue_09": (
            "Establishes Crane's £3,200 fraud motive through a codicil redirecting money to her "
            "account with a forged testator signature."
        ),
        "clue_10": (
            "Forthwright's annotation confirms he discovered Crane's forgery and intended to report "
            "it before week's end, creating immediate pressure to silence him."
        ),
        "clue_E3": (
            "Crane confesses Forthwright's ultimatum, her financial motive, and preparing foxglove "
            "extract in the greenhouse, completing the full murder narrative."
        ),
        "clue_M1": (
            "Supplies Morris's apparent revenge motive but places him continuously in the garden "
            "from two until the alarm, away from the poisoned tea."
        ),
        "clue_M2": (
            "Morris explicitly denies entering the house and offers a verifiable garden-bench "
            "alibi, excluding him from preparing or serving Forthwright's cup."
        ),
    },
    "H004": {
        "clue_W1": (
            "Records Wyle's false library alibi and denial of the decanter, directly contradicted "
            "by Ashby's three-o'clock eyewitness account."
        ),
        "clue_BU_key": (
            "Provides the controlled study key from Hedges's household ring, enabling lawful entry "
            "and showing the cooperative butler did not conceal access."
        ),
        "clue_BU1": (
            "Hedges places Drake continuously in the entrance hall from two-thirty past four, "
            "exonerating him despite the planted monogrammed glove."
        ),
        "clue_01": (
            "The absence of close-range powder stippling proves Orr's gunshot was not a contact "
            "suicide, exposing the revolver wound as post-poison staging."
        ),
        "clue_02": (
            "Bitter almond odour in Orr's brandy glass identifies hydrogen cyanide and points to "
            "poisoning rather than the visible gun wound."
        ),
        "clue_03": (
            "Confirms a lethal prussic-acid dose in the decanter sufficient to cause cardiac arrest "
            "within the exact post-delivery interval."
        ),
        "clue_04": (
            "The Drake-monogrammed glove is a planted false lead: its ownership is genuine, but "
            "Hedges's continuous alibi proves Drake never entered the study."
        ),
        "clue_05": (
            "Shows Wyle abused his exclusive custody of Orr's seal to forge operational orders, "
            "establishing access and the ongoing fraud."
        ),
        "clue_06": (
            "Orr's sealed letter exposes financial irregularities and summons the provost Thursday "
            "morning, giving Wyle an immediate deadline to prevent discovery."
        ),
        "clue_CK1": (
            "The inner-cabinet key provides the authenticated access path to Wyle's forged receipts "
            "and incriminating memorandum."
        ),
        "clue_07": (
            "Directly proves Wyle forged receipts and embezzled £1,800 through fourteen months of "
            "documents in his own handwriting."
        ),
        "clue_08": (
            "Wyle's own memorandum states the provost meeting would finish him and must not occur, "
            "documenting motive, knowledge, and urgency."
        ),
        "clue_O1": (
            "Mrs. Orr confirms the Admiral never drank in afternoons, proving the three-o'clock "
            "brandy was brought by someone else rather than requested or poured by Orr."
        ),
        "clue_AS1": (
            "Ashby independently places Wyle carrying the brandy decanter toward the study at three, "
            "directly linking him to delivery of the poison."
        ),
        "clue_D1": (
            "Records Drake's apparent promotion grievance and denial of study entry while explaining "
            "how his glove was available to be planted."
        ),
        "clue_D2": (
            "Drake invokes Hedges's independently confirmed entrance-hall alibi, conclusively "
            "separating him from both the study and staged glove evidence."
        ),
    },
    "H005": {
        "clue_03": (
            "Proves Beal's awl was planted: it bears no blood and matches no wound, eliminating the "
            "apparent weapon while exposing deliberate framing."
        ),
        "clue_04": (
            "Identifies a lethal single-sitting dose of antimony in Hartley's wine and explains the "
            "six-to-eight-hour delay before death."
        ),
        "clue_05": (
            "Identifies the hidden wine as a special private order through its merchant seal and "
            "yellow ribbon, enabling the bottle to be traced to Lunt."
        ),
        "clue_01": (
            "Rigor proves Hartley died on a flat surface and was moved to the stairs two hours later, "
            "establishing postmortem staging rather than an accidental fall."
        ),
        "clue_02": (
            "The absence of fall trauma and signs of systemic poisoning disprove accidental death "
            "and corroborate antimony as the true fatal mechanism."
        ),
        "clue_09": (
            "The merchant ledger directly traces a cash-paid private Bordeaux order from G. Lunt "
            "to Hartley's workshop on the murder afternoon."
        ),
        "clue_CR1": (
            "Crabb independently identifies Lunt as the cash buyer who ordered the distinctive "
            "bottle delivered privately to Hartley by four."
        ),
        "clue_11": (
            "Lunt's torn receipt matches the bottle's seal, ribbon, date, and order, physically "
            "linking his records to the poisoned wine at the workshop."
        ),
        "clue_10": (
            "The partnership deed establishes Lunt's concrete financial grievance: Hartley's solo "
            "client solicitation breached their contract and triggered penalties."
        ),
        "clue_L1": (
            "Records Lunt's false home alibi and attempt to minimize the partnership dispute, both "
            "contradicted by the bottle trail and confession."
        ),
        "clue_L4": (
            "Lunt confesses putting antimony in the delivered wine and moving Hartley's body after "
            "midnight, confirming motive, means, act, and staged staircase scene."
        ),
        "clue_LW1": (
            "Whitmore places Hartley healthy at seven, shortly before Lunt's eight-o'clock meeting, "
            "narrowing administration of the slow poison to Lunt's visit."
        ),
        "clue_B1": (
            "Beal admits returning at nine after their argument but says the stair door was shut "
            "and he never entered, an account later corroborated by the body position."
        ),
        "clue_B3": (
            "Beal saw no body at the staircase at nine, proving Hartley was moved there later and "
            "corroborating Lunt's post-midnight staging confession."
        ),
        "clue_B2": (
            "Explains Beal's awl was left for repair two weeks earlier and planted beside the body, "
            "removing the false physical link to Beal."
        ),
    },
}


def execute_plan(seed_id: str, *, commit: bool = False) -> dict:
    plan = PLANS[seed_id]
    client = DetectiveClient()
    session = client.start_session(seed_id)
    clues: dict[str, ClueText] = {}

    def remember(found: list[ClueText]) -> None:
        clues.update({clue.clue_id: clue for clue in found})

    for action in plan.actions:
        verb, *args = action
        if verb == "move":
            client.move(args[0])
        elif verb == "search":
            observation = client.search()
            for evidence in observation.found:
                remember(evidence.yields)
        elif verb == "interview":
            remember(client.interview(args[0]).said)
        elif verb == "present":
            observation = client.present(args[0], args[1])
            if not observation.accepted:
                raise RuntimeError(f"Expected accepted presentation failed: {action}")
            remember(observation.revealed)
        else:
            raise ValueError(f"Unknown action: {verb}")

    actual = frozenset(clues)
    if actual != plan.expected_clues:
        missing = sorted(plan.expected_clues - actual)
        unexpected = sorted(actual - plan.expected_clues)
        raise RuntimeError(f"Clue audit failed; missing={missing}, unexpected={unexpected}")
    if client.actions_remaining != plan.expected_actions_remaining:
        raise RuntimeError(
            f"Action audit failed: expected {plan.expected_actions_remaining}, "
            f"got {client.actions_remaining}"
        )

    if plan.culprit_id not in {member.id for member in session.briefing.cast}:
        raise RuntimeError("Planned culprit is absent from the live briefing")
    if plan.means_id not in {option.id for option in session.briefing.means_options}:
        raise RuntimeError("Planned means is absent from the live briefing")
    glosses = NOTE_GLOSSES[seed_id]
    if frozenset(glosses) != plan.expected_clues:
        raise RuntimeError("Evidence-note glosses do not exactly cover the audited clue set")
    notes = [
        {"clue_id": clue_id, "note": glosses[clue_id]}
        for clue_id in clues
    ]
    output: dict = {
        "seed_id": seed_id,
        "culprit_id": plan.culprit_id,
        "means_id": plan.means_id,
        "actions_remaining": client.actions_remaining,
        "clue_count": len(clues),
        "evidence_notes": notes,
        "process_explanation": plan.explanation,
    }
    if commit:
        result = client.commit(
            culprit_id=plan.culprit_id,
            means_id=plan.means_id,
            evidence_notes=notes,
            process_explanation=plan.explanation,
        )
        output["commit_result"] = result.model_dump()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an audited scored-seed action plan")
    parser.add_argument("seed", choices=sorted(PLANS))
    parser.add_argument("--commit", action="store_true")
    parser.add_argument(
        "--confirm-scored",
        action="store_true",
        help="Required with --commit because the server allows one submission per scored seed",
    )
    args = parser.parse_args()
    if args.commit and not args.confirm_scored:
        parser.error("--commit requires --confirm-scored")
    print(
        json.dumps(
            execute_plan(args.seed, commit=args.commit),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
