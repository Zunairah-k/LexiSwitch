"""Hand-written closed-class word lists (pronouns, postpositions, question words,
auxiliaries, conjunctions, common adverbs) for romanized Hindi and Telugu.

They override the dictionary built from the training lists, because the English
frequency list contains many romanized Hindi/Telugu function words.
Hindi was written for review by a Hindi speaker; the Telugu list should be
checked by a Telugu speaker.
"""

HINDI = """
hai hain hoon ho hoga hogi honge tha thi nahi nahin nhi
ka ke ki ko se mein par tak liye baad pehle saath bina
mera meri mere tera teri tere hamara hamari hamare tumhara tumhari tumhare uska uski uske apna apni apne
mujhe mujhko humein tumhe tumko unhe aap tum hum tu woh wo vo yeh ye
kya kyun kyu kaise kahan kab kaun kitna kitne kitni kaisa kaisi
aur lekin magar kyunki isliye agar toh bhi sirf abhi phir jab ab aaj kal parso
bahut bohot bahot bhot thoda thodi zyada bilkul sab sabhi kuch koi har ek
raha rahi rahe gaya gayi gaye hua hui hue kar karna karo chahiye sakta sakti sakte
yahan wahan idhar udhar kabhi kahin haan ji arre arey acha achha accha theek thik sahi bas aa
""".split()

TELUGU = """
nenu nuvvu meeru memu manam mana naa naaku nee neeku mee meeku maaku vaadu vaallu vallu vaadi vaari
idi adi ivi avi ila ala aa ee ki ku lo tho ni ga nundi nunchi kosam gurinchi meeda pai tarvata mundu
ippudu eppudu ekkada akkada ikkada ela enti enduku evaru emi entha
undi unnadi unnayi unnanu unnav unnaru unnam ledu kadu ayindi
chala konchem inka kani mari ra raa ante ayithe kooda kabatti repu ninna ivvala roju
""".split()

FUNCTION_WORDS = {"hi": sorted(set(HINDI)), "te": sorted(set(TELUGU))}