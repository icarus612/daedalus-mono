import React from "react";
// nodejs library that concatenates classes
import classNames from "classnames";
import { Link } from "react-router-dom";

// @material-ui/core components
import withStyles from "@material-ui/core/styles/withStyles";
// @material-ui/icons
import ArtTrack from "@material-ui/icons/ViewQuilt";
import Description from "@material-ui/icons/Description";
// core components
import Header from "components/Header/Header.jsx";
import Footer from "components/Footer/Footer.jsx";
import Button from "components/CustomButtons/Button.jsx";
import GridContainer from "components/Grid/GridContainer.jsx";
import GridItem from "components/Grid/GridItem.jsx";
import HeaderLinks from "components/Header/HeaderLinks.jsx";
import NavPills from "components/NavPills/NavPills.jsx";
import Parallax from "components/Parallax/Parallax.jsx";
import SectionCarousel from "./Sections/SectionCarousel.jsx";

import profile from "assets/img/Ellis.jpg";

import creation from "assets/Stories/yearsFromCreation.xls";
import hFordIsrael from "assets/Stories/henryFordAndIsrael.png";
import iBMHolocaust from "assets/Stories/IBMAndTheHolocaust.png";
import beast from "assets/Stories/markOfTheBeast.jpg";
import turin from "assets/Stories/shroudOfTurin.jpg";
import love from "assets/Stories/Love.doc";

import List from "@material-ui/icons/List";

import profilePageStyle from "assets/jss/material-kit-react/views/profilePage.jsx";

class ProfilePage extends React.Component {
  render() {
    const { classes, ...rest } = this.props;
    const imageClasses = classNames(
      classes.imgRaised,
      classes.imgRoundedCircle,
      classes.imgFluid
    );
    const navImageClasses = classNames(classes.imgRounded, classes.imgGallery);
    return (
      <div>
        <Header
          color="transparent"
          brand="The Wilderness Tabernacle of Witness"
          rightLinks={<HeaderLinks />}
          fixed
          changeColorOnScroll={{
            height: 200,
            color: "white"
          }}
          {...rest}
        />
        <Parallax filter image={require("assets/img/bg4.jpg")}>
          <div className={classes.container}>
            <GridContainer>
              <GridItem xs={12} sm={12} md={9}>
              <h1 className={classes.title}>
                Short Stories
              </h1>
              <h5 className={classes.title}>
                Not all stories told are told correctly. Here are some "FAQ's" and stories commonly mistold.
              </h5>
                {/*<br />
                <Button
                  color="danger"
                  size="lg"
                  href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <i className="fas fa-play" />Watch video
                </Button>*/}
              </GridItem>
            </GridContainer>
          </div>
        </Parallax>
        <div className={classNames(classes.main, classes.mainRaised)}>
          <div>
            <div className={classes.container}>
            <br />
            <br />
              <GridContainer justify="center">
                <GridItem xs={12} sm={12} md={12} lg={12} className={classes.navWrapper}>
                  <NavPills
                    alignCenter
                    color="info"
                    horizontal={{
                      tabsGrid: { xs: 12, sm: 4 },
                      contentGrid: { xs: 12, sm: 8 }
                    }}
                    tabs={[
                      {
                        tabButton: "When was Jesus Born?",

                        tabContent: (
                          <div>
                            <h3>When was Jesus Born?</h3>
                            <p>This is a question that has been asked for as long as I can remember.  I will warn you, if you are basing your opinion on the English translations or what you have been taught and not on the original text which is OT Hebrew and NT Greek, you might not understand the context of this article.

        The first question we must answer is who is Jesus?  This might sound strange, but if you base your answer on conventional thinking you have a lot of unanswered questions.  What does scripture say about who Jesus is?
        (John 10:30) I and the Father are one.”
        (1Cor 15:47)  The first MAN [Adam] (was) out-of earth made-of-dirt, the second MAN [Jesus] out-of heaven.
        (John 8:42)  The Jesus said therefore to-them, If the God was YOUR Father, YOU-were (likely) cherishing me, for I myself-came-out out-of the God and I-am-present; for neither have-I-come-and-am-still-come from myself, BUT that (one) dispatched me.
        (Acts 10:36) The word which he-dispatched to-the sons of-Israel himself-bringing-good-news peace through Jesus Messiah:  this (one) is Jehovah of-all.
        (John 8:23)  And he-said to-them, YOU yourselves-are out-of the (things) below, I myself-am out-of the-(things) above; YOU yourselves-are out-of this world.  I myself-am not out-of this world.
        (Mat 16:16)  But having-answered Simon Peter said, YOU yourself-are the Messiah, the son of-the God, namely-the living (one).
        There are many other verses but scripture clearly states that Jesus is God in the flesh, Jesus Messiah Jehovah.

        This brings up the first question.  If Jesus was in Mary’s belly for 9 months, then the triunity was out of commission  for  9 months.  Plus, you would have to agree with the Catholics and say that Mary is the mother of God.  On I-4 in Orlando FL the Catholics have a large gold sign, “MARY, QUEEN OF THE UNIVERSE”.  How can Mary be the mother of the creator of the universe?  They also teach that Mary is equal to Jesus, co-redemptor.

        Nowhere in the Greek text does it state that what was in Mary’s belly was a child.  The English translations call it a child but not the Greek text.
        (Matt 1:18)  For (as) his mother Mary (was) having-been-betrothed to-the Joseph, before they either came-together she-was-found having in womb out-of (the) Holy Spirit.  The word “child” is not in the Greek text.
        (Matt 1:20)  But (as) he (was) meditating these-(things), behold, (an) angel of-Jehovah appeared to-him by apparition, saying, Joseph, son of-David, might-you not fear-for-yourself to-take-along-to-yourself Mary your wife, for the-(thing) in her is having-been-begotten out-of (the) Holy Spirit.  The word “conceived” is not in the Greek text.
        (Matt 1:23)  Behold, the virgin will-have in womb, and she-will-bring-forth (a) son, and they-will-call his name Emmanuel, which is being-translated-with, the God with us.  The word “child” is not in the Greek text.

        So what is in Mary’s belly?   The book of Hebrews is very clear.
         (Heb 10:5)  On-this-account coming-in into the world he-is-saying: You-willed not sacrifice and offering, but you-yourself-rendered (a) body thoroughly-fit for-me;
        (Phil 2:7)  BUT he-emptied himself having-taken form of (a) slave, having-become in similitude of-MEN;
        Mary prepared a body for Jesus and he took on the form of a slave and entered the body just prior to delivery because He had to break the matrix to fulfil the law.
        (Luke 2:23)  According-as it-has-been-and-is-still-written in (the) law of-Jehovah, That every male thoroughly-opening (a) matrix will-be-called holy to-the Lord;

        Jesus is God in the flesh.  If He was born like you and me, He would have been born in sin as we are.  Every time Jesus is referred to in the New Testament in the form of a pronoun, it is always a plural pronoun indicating more than one, Father, Son, and Holy Spirit.

        Conclusion:
        Jesus is God in the flesh, creator of the universe.  A human being can not forgive the sins of the world.  He was not born into the world as you and me but  “came into the world” in a body prepared for Him.  So what day should we celebrate Jesus?  Everyday of course, as believers He dwells within us and is with us 365 days a year, 24 hours a day.  Very few people know who Jesus really is!!
        								</p>
                      </div>

                        )
                      },
                      {
                        tabButton: "Bible Translation History",
                        tabContent: (
                          <div>
                            <h3>Bible Translation History</h3>
                            <p>Romans 3:1-2 and II Timothy 3:16 tells us how we got the Holy Scriptures.  Romans 3  1. �What therefore the advantage of-the Jew or what the profit of-the circumcision? 2. Much according-to every manner. For first on-the-one-hand because they-were-trusted with the oracles (writings) of-the God.  II Timothy 3:16 �All scripture is God-breathed and profitable towards teaching, toward reproof, toward correction, toward discipline the discipline in justice�.  The Holy Scripture is given in three languages: the Old Testament in Hebrew, a small amount of Aromatic, and the New Testament in Greek.  The alphabets of the Hebrew and Aromatic are very close in appearance.



              The Bible has come to us through more than 40 writers under the inspiration of the Holy Spirit over a period of 1600 years and archaeologist have never found one piece of evidence to contradict Scripture, simply an amazing fact!



              The printing press was invented around 1450 AD; therefore, all copies of the Bible before that time were hand written.  A very small percent of the population before 1450 AD had a copy or even access to a copy of the Bible.



              When the Jews were making their hand copies they would count every �yod� which is a small letter in the Hebrew text that appears 66,420 times in the Old Testament.  If the number of yod�s were not correct they would discard that copy and start again.  Extreme caution was taken to insure accuracy.  Unfortunately, the same caution was not taken with the Greek text.  Even so there are very few major errors in the New Testament.  Most are minor spelling differences.  Some so call scholars have made a major issue of these errors but when the different texts are compared, the large number of errors are simply not there as claimed.  It is very easy for you to compare for yourself.  Whenever people make this claim, ask them to show you the errors.  They are usually are repeating what they have heard and not what they have learned for themselves.



              The Hebrew language dates back to at least the time of Abraham, since in Genesis 14:13 he is referred to as �the Hebrew�.  It was probably the language of the world population up to the tower of Babel.



              The Greek language according to the Encyclopedia Britannica dates back to about 900 BC and Greece ruled the total-inhabited-earth from approximately 336 BC to 63 BC.  Greek continued to be the common language even among the Jews.  Six translators from each of the twelve tribes of Israel were sent to Alexandria by Eleazar, the chief priest of Jerusalem, at the request of Ptolemy II Philadelphus (285-246 BC), a patron of literature.   They translated the Old Testament into Greek, called the Septuagint.



              The Latin language was developed by the Romans about 600 BC.  During the rule of the Roman Empire the languages were Greek and Latin.  The alphabet of the Greek and Latin languages are very similar in appearance.



              It is not necessary at this time to dwell on the Old Testament Hebrew since the Dead Sea Scholl�s have verified the accuracy of the known texts that are available.  One must realize that Hebrew is a very difficult language and will not be understood totally in my opinion until the Messiah returns and restores our understanding of Hebrew.



              The three oldest Greek manuscripts known today are as follows: 1. The Alexandrian which belongs to the Church of England and is kept in the British Museum.  2. The Vatican which is in the Vatican Library in Rome.  3. The Sinaitic which is the treasure of the Greek Church at St. Petersburg.  These manuscripts date back to between 300 and 450 AD.  The Vatican manuscript is not available to the public for examination or study.



              The first major translation from the original Hebrew and Greek to Latin was made by Eusebius Hieronymus better known to us as Saint Jerome. He lived in Bethlehem and was considered to be one of the great scholars and holiest men of his day.  The request for this translation was made by St. Damasus I who was the Pope of the Catholic Church from 366 � 384 AD.  The New Testament was completed in 385 AD and the Old Testament shortly thereafter.  This translation is known as the Latin Vulgate.



              An interesting note about Pope Damasus I from a book sanctioned by the Catholic Church entitled �The Popes� by Michael Walsh is that he hired an army of thugs that stormed the basilica in October 366 A. D. where the antipope Ursinus was located and 150 were killed.   The book �The Popes� states, �So Damasus destroyed his enemies by using violence in an age of violence�.  This history can be found on pages 42-45 in �The Popes�  It is certainly worth reading.



              Most people that have studied the Catholic Church believe it officially began when Constantine held the Council of Nicaea in 325 AD and adopted Christianity as well as Paganism as state religions.  He had learned that man has always used some form of religion to control the masses.



              Also during this time Emperor Theodosius of Rome declared Christianity the state religion (Feb. 27, 380 AD).  This was probably one of the biggest disasters in Church history since all pagans were required to join the Church under orders of Emperor Theodosius whether they wanted to or not.  They brought all their pagan practices with them.



              For the next one thousand years there were no significant complete translations of the Scriptures made, only portions.  The Catholic Church dominated the total-inhabited-earth during this period of time.  In fact at the Council of Trent in 1545 the Church decided �Why should it yield to Greek and Hebrew manuscripts, which have been for all these hundreds of years in the hands of Jewish unbelievers and Greek schismatics?�  They decreed in council that the old Vulgate should be regarded as the standard text, in other words the inspired text.



              The next major translation was by John Wycliffe (1330 � 1384 AD) The Wycliffe Bible was only a translation of a translation.  It was based on the Latin Vulgate of St. Jerome.  Wycliffe was not capable of working in the original Greek and Hebrew even if he had access to them; in fact, there was probably not a man in England at the time capable of doing so.  Wycliffe�s translation was made for the plain people.  He stated, �The Sacred Scriptures are the property of the people, and one which no one should be allowed to wrest from them . . . Christ and His apostles converted the world by making known the Scriptures to men in a form familiar to them . . . and I pray with all my heart that through doing the things contained in this book we may all together come to the everlasting life.�



              The Catholic Church did not receive Wycliffe�s translation very well at the time.  A bill was brought before Parliament to forbid the circulation of the Scriptures in English.

              The rulers of the Catholic Church were determined to prevent the circulation to his translation.  After Wycliffe�s death, Archbishop Arundel complained to the Pope of �that pestilent wretch, John Wycliffe, the son of the old Serpent the forerunner of Antichrist, who had completed his iniquity by inventing a new translation of the Scriptures�.  Readers that were caught with copies to Wycliffe�s Bible were burned with the copies around their necks, husbands were made to witness against their wives, children forced to light the death-fires of their parents, and possessors of the banned Bible were hunted down as if they were wild beasts.



              In May 1378 the Catholic Church assembled for the trial of John Wycliffe, the parish Priest of Lutterworth.  The power of his enemies had grown rapidly, even the King of England.  Twice already the arraignment of Wycliffe had been strangely interrupted when on this third occasion an earthquake hit the City of London.  So determined were they to proceed that Archbishop Courtenay stated, �No! We will not give up the trial.  This earthquake but portends the purging of the kingdom; for as there are in the bowels of the earth noxious vapors which only by a violent earthquake can be purged away, so are there evils brought by such men upon this land which only by a very earthquake can ever be removed.  Let the trial go forward!�



              After three days of deliberation Wycliffe�s teachings were condemned and he was excommunicated from the Catholic Church and the Church of England.  On the last Sunday of 1384, his little flock at Lutterworth was kneeling in hushed reverence before the altar, John Wycliffe had a stroke.  He died on the last day of the year.



              Forty years afterwards, by a decree of the Council of Constance, John Wycliffe�s bones were dug up and burned, and the ashes flung into the little river Swift, which � runneth hard by his church at Lutterworth�.



              Remember, there were still no printing presses.  It took Wycliffe�s copyist 10 months to complete one copy.  Even so, after 600 years there are still some one hundred and seventy copies remaining.  John Wycliffe made a difference in his time.



              In November 1454 came the invention of movable type in printing.  In May 1454 came the fall of Constantinople, and crowds of Greek scholars were driven for refuge to Western Europe, teaching the language of the rediscovered classics, the language in which the New Testament was written.  �The Renaissance� had come, the revival of learning in Europe.



              And with it came the revival of the study of Greek and Hebrew.  The first Greek grammar was published in 1476 and the first Hebrew grammar in 1503.  Then came Erasmus, a great Greek scholar, a friend of Sir Thomas More, and he began the study of the best old manuscripts he could find and so gave the world in 1516 his famous Greek New Testament.  His manuscripts were not very ancient or valuable; consequently, his New Testament was not perfect but it was the beginning.



              There is one major difference between the Latin and Greek languages that should be understood, the article �the�.  There is not an article �the� in the Latin language.  A. T. Robertson in his 1934 book published by Broadman Press entitled �A Grammar of the Greek New Testament in the Light of Historical Research�, makes a tremendous comment.  He states, �A Greek Contribution.  The development of the Greek article is one of the most interesting things in human speech.  Among the Indo-Germanic languages it is �a new Greek departure�.  It is not found in Sanskrit nor in Latin.�  He further states, �The article is associated with a gesture and aids in pointing out like an index finger.  It is a pointer.  Whenever the Greek article occurs, the object is certainly definite.  When it is not used, the object may or may not be. The article is never meaningless in Greek.�



              The article �the� appears over 17,000 times in the Greek text. The next most used word in the New Testament is �and� and is used over 9,000 times.  Most English translations have less than one half the articles �the� and in many cases it is used and should not have been.  The reason the article �the� is left out is the fact that a large number of the early English translations relied heavily on the Latin Vulgate, which again does not have an article �the�.



              First the Printing Press; next the revival of Greek learning; then Erasmus� Greek New Testament; and now at this critical period came forth the man who was to use these new powers to make the first English translation of the New Testament from the Greek.  William Tyndale was born in 1483.  He studied at Cambridge with Erasmus about the time of Erasmus� Greek New Testament.  It seems this was an inspiration to Tyndale.  In a conversation with an opponent the following comments were made:  �We had better,� said his opponent, �be without God�s laws than the Pope�s.� Tyndale stated, �I defy the Pope, and all his laws; and if God spare me I will one day make the boy that drives the plough in England to know more of Scripture than the Pope does.�



              Tyndale knew that without the sanction of the Church of England no publisher would dare to print his translation that he had already started.  He asked Cuthbert Tonstal, Bishop of London, for permission to carry on his work in his household under his lordship�s patronage but the Bishop said his house was full.



              It was a troubled time in the Church of England as well as during the reign of Henry VIII (King of England 1509 � 1547) who was supposed to be a Christian.  Martin Luther had just nailed his thesis to the church door and burned the Papal bull.  Luther was excommunicated on April 17, 1521.   In 1524, Tyndale decides to leave his native land, never to see it again.  He went to Hamburg, in poverty and distress, and under constant danger he worked at his translation so diligently that the following year he was in Cologne with the pages of his New Testament.  Word of this English edition of the New Testament reached the Bishops of England and Tyndale escaped with his unfinished copies to Worms where the printing was complete.  A German scholar and friend of Tyndale�s writes in his diary that Tyndale could speak seven languages � Hebrew, Greek, Latin, Italian, Spanish, English, French � as his native tongue (German is taken for granted).



              Why were so many so called Christians opposed to individuals like Wycliffe and Tyndale?  A very good explanation is found in J. Paterson Smyth�s book �How we Got Our Bible� copyright 1899.  �You need to realize that the Church was the sacred thing, the Devine Society founded by her Lord, coming down through all the ages, one body, the center of unity, the dispenser of the Holy Sacraments, the teacher of the people in their holy faith.  The Church with all her faults was still the central fact and any disturbing of her foundations would be fatal to religion.�  People like Sir Thomas More wanted translations but felt they had to be made by Catholic-minded men (loyal Churchmen).  Some things never change.



              Sir Thomas More called Tyndale, �a beast, as one of the hell-hounds that the devil hath in his kennel, discharging a filthy foam of blasphemies out of his brutish beastly mouth, a deceiver, a hypocrite, puffed up with the poison of pride, malice and envy.�  Yet the best that More could summon against Tyndale, when all is boiled down, is that he translated the Greek word for �elder� as �elder� (not priest) and the Greek word for �repentance� as �repentance� (not �do penance�), the Greek word for �congregation� as �congregation� (not church), �charity� became �love�, �confess� became acknowledge.  Even Erasmus, More�s friend, translated the Greek ekklesia as congregation, not �church�.



               We also now know that agapoa should be translated charity and philio as love.  We know this from actual Greek writings. In a statement by Antonius over the body of Caesar he said  �You loved (philio) him as a father and you cherished (agapoa) him as a benefactor.�  This confirms how the Greeks and Romans used philio and agapoa.



              Tyndale continued to update his translation as he learned more about the Greek language until the final edition of 1534 as we have it today.



              In 1535, an English clergyman, Henry Phillips, betrayed him to the Antwerp authorities and had him kidnapped.  He was imprisoned at Vilvorde, near Brussels, Germany for sixteen months.  A letter from him, in Latin, has survived:



              I suffer greatly from cold in the head, and am afflicted by a perpetual catarrh, which is much increased in this cell . . . My overcoat is worn out; my shirts are

              also worn out . . . And I ask to have a lamp in the evening: it is indeed wearisome

              sitting alone in the dark.  But most of all I beg and beseech you clemency to be urgent with the commissary, that he will kindly permit me to have my Hebrew Bible, Hebrew Grammar, and Hebrew Dictionary, that I may pass the time in the study.



              Even Thomas Cromwell, the most powerful man next to King Henry VIII, moved to get him released: but Philips in Belgium, acting for the papal authorities, blocked the moves.  On the morning of October 6, 1536, William Tyndale was taken to the place of execution, tied to the stake, strangled and burned.  His last words were, �Lord open the King of England�s eyes.�



              In 1535, we have the translation of Myles Coverdale who became the Bishop of Exeter.  His Bible makes no pretence to be an original translation; it is �translated out of Douche and Latin into English, with the help of five translators,� and evidently one is Tyndale who he follows very closely in the New Testament.  But ekklesia is now church.



              In 1537, came �Matthews� Bible� which was really prepared by John Rodgers. It was simply a translation taken from Tyndale except the last half of the Old Testament, which was taken from Coverdale.  Tyndale had not finished the Old Testament.  Rodgers did not put his name in the translation because of his close occasion to Tyndale.  John Rodgers was martyred during the reign of Queen Mary, daughter of Henry VIII, who ruled from 1553 � 1558.



              Archbishop Cranmer and some of the chief advisers to Henry VIII were determined to have a translation that would be really worthy of its position as a National Bible.  Myles Coverdale was selected to take charge of the work. He along with the Kings printer went to Paris so that �the book might be brought out in the best possible style�.  Henry had broken away from the Catholic Church by this time (he wanted to divorce his wife).  All the Bibles were seized by the �Lieutenant Criminall� but Coverdale managed to carry the printing press, the type, and the printers themselves back to England to finish the work in April 1539.  It became known as the Great Bible, but was little more than a combination of the Mathews� and Coverdale Bibles.  Ekklesia is still church.



              After Queen Mary took the throne in 1553, because of her close ties to the Catholic Church, most of the Bible scholars left England and moved to Geneva.  It was here that they translated the Geneva Bible which became famous as the �Breeches Bible� because of its translation of Genesis 3:7 where Adam and Eve � sewed fig-tree leaves together, and made themselves breeches�.  It was first printed in 1560 and this was the first time the chapters were divided into verses and they omitted the Apocrypha.  It had marginal notes for better understanding of obscure passages, cross-references, concordances, maps, and picture illustrations.  It was of lower price as well as smaller and easier to carry than the Great Bible.  It became the most popular Bible that had ever appeared in England until that time.



              In mid 1560, the Archbishop of Canterbury, Matthew Parker, called together about a dozen bishops, scholars and dignitaries to revise King Henry VIII�s �Great Bible�.  Published in 1568, it was more lavish and expensive � even bigger than the Great Bible.  It was printed as a lectern Bible with few marginal notes, definitely intended for the private reader.  It became known as the Bishops� Bible and was definitely translated in the direction by clergy that still believed that the true Bible was the Latin version.  It was not popular.



              As a result of the popularity of the Geneva or Breeches Bible, in January, 1604, a conference of bishops and clergy was held in the drawing rooms of Hampton Court Palace, under the presidency of King James himself. He publicly denounced the Geneva Bible and told the translators, �that no notes should be added, having found in those which were annexed to the Geneva translation some notes very partial, untrue, seditious, and savoring too much of dangerous and traitorous conceits�.  One passage that really disturbed King James was in the first chapter of Exodus, which describes the conduct of the Hebrew midwives, who �did not as the king of Egypt commanded, but saved the men-children alive�.  Since King James was supposed to be divine, he declared, �It is false, to disobey a king is not lawful; such traitorous conceits should not go forth among the people.�  The translators were instructed to use the Bishops� Bible as a basis for their revision.  This is the most Latinate of all the translations, which explains the poor translation of the article �the� since the Latin does not have an article �the�.  The King James version was the first to translate pascha (Passover) as Easter in Acts 12:4.  Near the end of the Preface �The Translators To The Reader�, the translators state that they chose to translate thought for thought instead of word for word.  The only problem with this is that the Lord said, � My thoughts are not your thoughts� (Isaiah 55:8).  This translation was complete in 1611 but was never authorized: it had no royal seal upon it at all.  Being called an �Authorised� version did not start until the 1760s.



              One of the great Hebrew scholars of the day, Broughton, wrote to King James that he �would rather be torn asunder by wild horses than allow such a version to be imposed on the Church�.

              `

              Between 1611 and 1880, there were about 70 translations, but mostly these were re-translations of translations and none appear to be much different from the King James.



              On February 10, 1870, Bishop Wilberforce rose in the Upper House of the Southern Convocation to propose, �That a committee of both Houses be appointed, with power to confer with any committee that may be appointed by the Convocation of the Northern Province, to report on the desirableness of a revision of the Authorized Version of the New Testament, whether by marginal notes or otherwise, in all those passages where plain and clear error. Whether in the Greek text adopted by the translators, or in the translations made from the same, shall on due investigation be found to exist.�



              In June 1870, the translators assembled in the Jerusalem Chamber in Westminster Abby in London, England to begin their work.  There were English scholars such as Alford, Stanley, Lightfoot, Westcott, Hort, to name a few.  Their stated purpose of the Convocation was �to introduce as few alterations as possible in the text of the Authorized Version�.



              The book � How We Got Our Bible� 1899, sums up the goal of the revisers.  �A scrupulous attention to the force of the Greek article, the different tenses of verbs, and the delicate shades of meaning in particles and prepositions, will account for many of the minor changes, which, though they may seem at first sight trifling and unnecessary, will often be found to affect seriously the meaning of a passage.  The revises also claim to have avoided the practice, adopted in the Authorized Version, of translating for the sake of euphony the same Greek word by different English words.�  The word euphony means, �the acoustic effect produced by words so formed and combined as to please the ear�.  Sounds like II Timothy 4:3 � itching ears.



              There was also an American committee that reviewed the revision.  A major change; the Lords� name was put back into the scriptures � Jehovah.  When the Greek word Kurios appears without the article �the� it should be translated Jehovah.  With the article it is translated �the Lord�. This translation is without question the best translation up until that time.    The American version is known as the 1901 American Standard.



              A clerk at Waldenbooks told me recently they have over 5,000 listings under Bibles.  There are close to 100 different English translations.  If you believe the Hebrew and Greek are divinely inspired, I wonder which one of these English translations is correct?



               Most language translators will tell you that before you make a translation from one language to another language you need a dictionary.  In the case of Greek to English, you will know with a dictionary what English word or combination of words to use for each Greek word.  Is it important to consistently translate each Greek word the same way each time it appears?  Revelations 22:18,91 tells us not to �add to� or �take away� from the scriptures.  That is plain enough for me, the scriptures should be translated as consistently and accurately as possible.



              None of the translations that I researched could I find any indication that a dictionary was used to assure each Greek word was consistently translated to the same English word with the possible exception of William Tyndale.  We know that when he was imprisoned at Vilvorde, near Brussels, he requested his Hebrew dictionary but no mention of a Greek dictionary.



              My first exposure to a consistently translated New Testament was in November, 1984.  Mr. Ralph H. Mount of Morriston, Florida translated it.  For twenty years before this time Mr. Mount had been preparing Bible study courses which were basically word studies.  He understood the problem that had existed with the English translations.



              He completed a Greek-English Dictionary in September, 1980 and an English-Greek Dictionary, in October, 1980.  In 1985, the translation of A Consistent New Testament was completed in hand printed letters.  A printed �study text� was made available in November of 1987.  In 1990 a new printing was made with the King James Version alongside of A Consistent New Testament.



              What does a consistent translation really mean?  Let us look at how the Greek word logos (lo�gos) which should be translated  �word� in English, has been translated.  In John 1:14, �The word (lo�gos) was made flesh, and dwelt among us.�  The King James translators translated the word logos (lo�gos) as follows: account (8x), cause (1x), communication (3x), doctrine (1x), fame (1x),intent (1x), matter (4x), mouth (1x), preaching (1x), question (1x), reason (2x), rumour (1x), saying (50x), tidings (1x), treatise (1x), utterance (4x), word (208x),Word (7x), work (2x).  Why all these different English words for one Greek word?



              There are literally thousands of other examples of inconsistent translating and you should consult a Young�s Concordance for proof of this.



              As you probably know it is very hard to find a Young�s Concordance in the bookstores,  but the Strong�s Concordance is available at almost all bookstores.  The Young�s Concordance was copyright in 1890 and the Strong�s Concordance was copyright in1892.  In my opinion, it only took Zeus or Satan two years to corrupt an excellent work done by Dr. Young.



              How important is it to study the Lord�s word?  Ralph Mount told me one time that if you had someone that you really cared about wrote you a 1000 page letter, would you read it?  What if it was in Greek and you could not read Greek?  You would not only get it translated but you would make sure it was done properly so you would get the true meaning of what the individual was saying to you.  So if your salvation is important, it is going to take a little effort on your part to learn the truth.



              Ask yourself a question, �Does what I know about scripture come from what I have been told by others or from what I have learned from studying for myself.�</p>
                          </div>

                        )
                      },
                      {
                        tabButton: "What Does John 3:16 Really Say?",
                        tabContent: (
                          <div>
                            <h3>What Does John 3:16 Really Say?</h3>
                            <p>
                            This verse appears in public more than any other verse in scripture; sporting events, billboards, graffiti, etc.  It appears to be everywhere.  It is normally used to say that the God loves everyone but is that what John 3:16 and scripture really teach us?



                            Read John 3:16, For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.   The verse is very clear, it states that He 'loved' the world, pass tense, not present  or future tense.  He loved it in the past and He sent His Son to redeem!  If He loves everyone then why does John 3:36 say the opposite, He that believeth on the Son hath everlasting life: and he that believeth not the Son shall not see life; but the wrath of God abideth on him.



                            What is frighten about this situation is the extremes that people will go to change scripture to make it say what they want it to say.  An example is an article published by the Southern Baptist Convention in Nashville, Tennessee.  It is as follows:

                            Think About This

                            God loves you.  He loves you so much

                            �that he gave his only begotten Son, that

                            whosoever believeth in him should not

                            perish, but have everlasting life� (John 3:16)



                            That is not what John 3:16 states!!  They changed loved (past tense) to loves (present tense).



                            Billy Graham has stated many times that John 3:16 is his favorite verse in scripture and that God loves everyone, He hates sin but loves the sinner.



                            The Lord loves the believer but I am still waiting for someone to show me one verse in scripture that states He loves everyone.



                            For more information on the word �Love� refer to �Short Bible Studies.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "Marriage - One Flesh",
                        tabContent: (
                          <div>
                            <h3>Marriage - One Flesh</h3>
                            <p>
                            On October 1, 2011 my wife, Dianne and I will have been married for 45 years.  For many years I have wondered why many married couples have such a problem making their marriage last.  The last time I checked many years ago the divorce rate was 58 per cent and of that 42 per cent left, 75 per cent were emotionally divorced but remain married because of kids, relatives, etc.  I just read an excerpt from a book by author Iris Krasnow entitled “The Secret Lives of Wives: Women Share What It Really Takes To Stay Married”.  This article confirms the last statement that about 10% of marriages are really happy.  Based on her comments, the author has not figured it out either.  After many years of thought (45 to be exact) I believe I have a better understanding of how to have a good marriage.

                            Ephesians 5:31 states, “Instead-of this (a) MAN shall-leave-behind the father and the mother and he-shall-be-very-united to his wife and the two shall-be with-reference-to flesh, one.



                            How does a man and women become one flesh?  For a long time I thought this was made possible by the husband and wife having children.  Although this might be part of the answer I believe it goes much deeper.

                            Genesis 2:21 KJ“and the LORD God caused a deep sleep to fall upon Adam, and he slept: and he took one of his ribs, and closed up the flesh instead thereof;” 22And the rib, which the LORD God had taken from man, made he a woman, and brought her unto the man.



                            The Hebrew word translated rib in the King James is “tsela” (6763 concordance reference).  The KJ translates this Hebrew word as follows – beam 1 time, board 2, chamber 2, corner 2, halting 1, leaf 1, plank 1, rib 2, side 19, side chamber 9, another 1, one 1.  No wonder there is confusion in the translations. Genesis 2 is the only two times the Hebrew word “tsela” is translated rib.  Tsela should be translated “side of” or “part of”.  This changes how this verse is understood.  As a kid I wondered why if the God took out a rib from Adam why I was not missing a rib since I am suppose to be in Adams’ image.

                            When the God created Adam, he was created with all the characteristics, emotions, etc. of both men and women.  When the God created woman He took a “side of” or a “part of” Adam and made a woman.  Now man and woman are trying to complete themselves and become one flesh again through marriage.  When you consider the many different characteristics of men and women you have to wonder how they ever make it together, but they have the God given desire to become one flesh.  Not knowing his religion, I was explaining this to a Catholic Church member not long ago and he stated, “That is why we have so much trouble in our Priesthood today”.  I do not know very many homosexuals or lesbians personally but they do not appear to be enjoying happiness as I know it.  They can never truly be one flesh with same sex relations.

                            I believe that if more people understood this principle they could better chose a mate they could spend a lifetime with.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "Does God Love Everyone?",
                        tabContent: (
                          <div>
                            <h3>Does God Love Everyone?</h3>
                            <p>
                            Read the verses below and then show me one verse that says God loves everyone.  Remember, John 3:16 is passed tense, “For God so loved the world…”  not present or future tense.



                            (Numbers 16:46)  And Moses said unto Aaron, Take a censer, and put fire therein from off the altar, and put on incense, and go quickly unto the congregation, and make an atonement for them: for there is wrath gone out from the LORD; the plague is begun.



                            (Deuteronomy 9:3)  Understand therefore this day, that the LORD thy God is he which goeth over before thee; as a consuming fire he shall destroy them, and he shall bring them down before thy face: so shalt thou drive them out, and destroy them quickly, as the LORD hath said unto thee.



                            (Deuteronomy 32:39)  See now that I, even I, am he, and there is no god with me: I kill, and I make alive; I wound, and I heal: neither is there any that can deliver out of my hand.

                            (Deuteronomy 32:40)  For I lift up my hand to heaven, and say, I live for ever.

                            (Deuteronomy 32:41)  If I whet my glittering sword, and mine hand take hold on judgment; I will render vengeance to mine enemies, and will reward them that hate me.

                            (Deuteronomy 32:42)  I will make mine arrows drunk with blood, and my sword shall devour flesh; and that with the blood of the slain and of the captives, from the beginning of revenges upon the enemy.

                            (Deuteronomy 32:43)  Rejoice, O ye nations, with his people: for he will avenge the blood of his servants, and will render vengeance to his adversaries, and will be merciful unto his land, and to his people.



                            (Leviticus 10:1)  And Nadab and Abihu, the sons of Aaron, took either of them his censer, and put fire therein, and put incense thereon, and offered strange fire before the LORD, which he commanded them not.

                            (Leviticus 10:2)  And there went out fire from the LORD, and devoured them, and they died before the LORD.



                            (2 Chronicles 34:21)  Go, enquire of the LORD for me, and for them that are left in Israel and in Judah, concerning the words of the book that is found: for great is the wrath of the LORD that is poured out upon us, because our fathers have not kept the word of the LORD, to do after all that is written in this book.



                            (Psalms 5:5)  The foolish shall not stand in thy sight: thou hatest all workers of iniquity.

                            (Psalms 5:6)  Thou shalt destroy them that speak leasing: the LORD will abhor the bloody and deceitful man.



                            (Psalms 7:11)  God judgeth the righteous, and God is angry with the wicked every day.



                            (Psalms 11:5)  The LORD trieth the righteous: but the wicked and him that loveth violence his soul hateth.



                            (Psalms 59:13)  Consume them in wrath, consume them, that they may not be: and let them know that God ruleth in Jacob unto the ends of the earth. Selah.



                            (Psalms 60:12)  Through God we shall do valiantly: for he it is that shall tread down our enemies.



                            (Psalms 146:8)  The LORD openeth the eyes of the blind: the LORD raiseth them that are bowed down: the LORD loveth the righteous:



                            (Proverbs 1:26)  I also will laugh at your calamity; I will mock when your fear cometh;

                            (Proverbs 1:27)  When your fear cometh as desolation, and your destruction cometh as a whirlwind; when distress and anguish cometh upon you.

                            (Proverbs 1:28)  Then shall they call upon me, but I will not answer; they shall seek me early, but they shall not find me:

                            (Proverbs 1:29)  For that they hated knowledge, and did not choose the fear of the LORD:

                            (Proverbs 1:30)  They would none of my counsel: they despised all my reproof.

                            (Proverbs 1:31)  Therefore shall they eat of the fruit of their own way, and be filled with their own devices.

                            (Proverbs 1:32)  For the turning away of the simple shall slay them, and the prosperity of fools shall destroy them.

                            (Proverbs 1:33)  But whoso hearkeneth unto me shall dwell safely, and shall be quiet from fear of evil.



                            (Proverbs 8:17)  I love them that love me; and those that seek me early shall find me.



                            (Proverbs 15:9)  The way of the wicked is an abomination unto the LORD: but he loveth him that followeth after righteousness.



                            (Isaiah 10:5)  O Assyrian, the rod of mine anger, and the staff in their hand is mine indignation.

                            (Isaiah 10:6)  I will send him against an hypocritical nation, and against the people of my wrath will I give him a charge, to take the spoil, and to take the prey, and to tread them down like the mire of the streets.



                            (Isaiah 22:17)  Behold, the LORD will carry thee away with a mighty captivity, and will surely cover thee.

                            (Isaiah 22:18)  He will surely violently turn and toss thee like a ball into a large country: there shalt thou die, and there the chariots of thy glory shall be the shame of thy lord's house.

                            (Isaiah 22:19)  And I will drive thee from thy station, and from thy state shall he pull thee down.



                            (Isaiah 63:6)  And I will tread down the people in mine anger, and make them drunk in my fury, and I will bring down their strength to the earth



                            (Isaiah 66:15)  For, behold, the LORD will come with fire, and with his chariots like a whirlwind, to render his anger with fury, and his rebuke with flames of fire.

                            (Isaiah 66:16)  For by fire and by his sword will the LORD plead with all flesh: and the slain of the LORD shall be many.



                            (Jeremiah 7:20)  Therefore thus saith the Lord GOD; Behold, mine anger and my fury shall be poured out upon this place, upon man, and upon beast, and upon the trees of the field, and upon the fruit of the ground; and it shall burn, and shall not be quenched.



                            (Jeremiah 13:14)  And I will dash them one against another, even the fathers and the sons together, saith the LORD: I will not pity, nor spare, nor have mercy, but destroy them.



                            (Jeremiah 21:10)  For I have set my face against this city for evil, and not for good, saith the LORD: it shall be given into the hand of the king of Babylon, and he shall burn it with fire.



                            (Jeremiah 25:33)  And the slain of the LORD shall be at that day from one end of the earth even unto the other end of the earth: they shall not be lamented, neither gathered, nor buried; they shall be dung upon the ground.



                            (Jeremiah 30:23)  Behold, the whirlwind of the LORD goeth forth with fury, a continuing whirlwind: it shall fall with pain upon the head of the wicked.

                            (Jeremiah 30:24)  The fierce anger of the LORD shall not return, until he have done it, and until he have performed the intents of his heart: in the latter days ye shall consider it.



                            (Jeremiah 36:7)  It may be they will present their supplication before the LORD, and will return every one from his evil way: for great is the anger and the fury that the LORD hath pronounced against this people.



                            (Jeremiah 44:27)  Behold, I will watch over them for evil, and not for good: and all the men of Judah that are in the land of Egypt shall be consumed by the sword and by the famine, until there be an end of them.

                            (Jeremiah 44:28)  Yet a small number that escape the sword shall return out of the land of Egypt into the land of Judah, and all the remnant of Judah, that are gone into the land of Egypt to sojourn there, shall know whose words shall stand, mine, or theirs.

                            (Jeremiah 44:29)  And this shall be a sign unto you, saith the LORD, that I will punish you in this place, that ye may know that my words shall surely stand against you for evil:



                            (Lamentations 2:1)  How hath the Lord covered the daughter of Zion with a cloud in his anger, and cast down from heaven unto the earth the beauty of Israel, and remembered not his footstool in the day of his anger!

                            (Lamentations 2:2)  The Lord hath swallowed up all the habitations of Jacob, and hath not pitied: he hath thrown down in his wrath the strong holds of the daughter of Judah; he hath brought them down to the ground: he hath polluted the kingdom and the princes thereof.

                            (Lamentations 2:3)  He hath cut off in his fierce anger all the horn of Israel: he hath drawn back his right hand from before the enemy, and he burned against Jacob like a flaming fire, which devoureth round about.

                            (Lamentations 2:4)  He hath bent his bow like an enemy: he stood with his right hand as an adversary, and slew all that were pleasant to the eye in the tabernacle of the daughter of Zion: he poured out his fury like fire.

                            (Lamentations 2:5)  The Lord was as an enemy: he hath swallowed up Israel, he hath swallowed up all her palaces: he hath destroyed his strong holds, and hath increased in the daughter of Judah mourning and lamentation.

                            (Lamentations 2:6)  And he hath violently taken away his tabernacle, as if it were of a garden: he hath destroyed his places of the assembly: the LORD hath caused the solemn feasts and sabbaths to be forgotten in Zion, and hath despised in the indignation of his anger the king and the priest.

                            (Lamentations 2:7)  The Lord hath cast off his altar, he hath abhorred his sanctuary, he hath given up into the hand of the enemy the walls of her palaces; they have made a noise in the house of the LORD, as in the day of a solemn feast.

                            (Lamentations 2:8)  The LORD hath purposed to destroy the wall of the daughter of Zion: he hath stretched out a line, he hath not withdrawn his hand from destroying: therefore he made the rampart and the wall to lament; they languished together.

                            (Lamentations 2:9)  Her gates are sunk into the ground; he hath destroyed and broken her bars: her king and her princes are among the Gentiles: the law is no more; her prophets also find no vision from the LORD.



                            (Lamentations 2:22)  Thou hast called as in a solemn day my terrors round about, so that in the day of the LORD'S anger none escaped nor remained: those that I have swaddled and brought up hath mine enemy consumed.



                            (Lamentations 3:43)  Thou hast covered with anger, and persecuted us: thou hast slain, thou hast not pitied.



                            (Lamentations 4:11)  The LORD hath accomplished his fury; he hath poured out his fierce anger, and hath kindled a fire in Zion, and it hath devoured the foundations thereof.

                            (Lamentations 4:12)  The kings of the earth, and all the inhabitants of the world, would not have believed that the adversary and the enemy should have entered into the gates of Jerusalem.

                            (Lamentations 4:13)  For the sins of her prophets, and the iniquities of her priests, that have shed the blood of the just in the midst of her,

                            (Lamentations 4:14)  They have wandered as blind men in the streets, they have polluted themselves with blood, so that men could not touch their garments.

                            (Lamentations 4:15)  They cried unto them, Depart ye; it is unclean; depart, depart, touch not: when they fled away and wandered, they said among the heathen, They shall no more sojourn there.

                            (Lamentations 4:16)  The anger of the LORD hath divided them; he will no more regard them: they respected not the persons of the priests, they favoured not the elders.



                            (Ezekiel 5:8)  Therefore thus saith the Lord GOD; Behold, I, even I, am against thee, and will execute judgments in the midst of thee in the sight of the nations.

                            (Ezekiel 5:9)  And I will do in thee that which I have not done, and whereunto I will not do any more the like, because of all thine abominations.

                            (Ezekiel 5:10)  Therefore the fathers shall eat the sons in the midst of thee, and the sons shall eat their fathers; and I will execute judgments in thee, and the whole remnant of thee will I scatter into all the winds.

                            (Ezekiel 5:11)  Wherefore, as I live, saith the Lord GOD; Surely, because thou hast defiled my sanctuary with all thy detestable things, and with all thine abominations, therefore will I also diminish thee; neither shall mine eye spare, neither will I have any pity.

                            (Ezekiel 5:12)  A third part of thee shall die with the pestilence, and with famine shall they be consumed in the midst of thee: and a third part shall fall by the sword round about thee; and I will scatter a third part into all the winds, and I will draw out a sword after them.

                            (Ezekiel 5:13)  Thus shall mine anger be accomplished, and I will cause my fury to rest upon them, and I will be comforted: and they shall know that I the LORD have spoken it in my zeal, when I have accomplished my fury in them.

                            (Ezekiel 5:14)  Moreover I will make thee waste, and a reproach among the nations that are round about thee, in the sight of all that pass by.



                            (Ezekiel 6:11)  Thus saith the Lord GOD; Smite with thine hand, and stamp with thy foot, and say, Alas for all the evil abominations of the house of Israel! for they shall fall by the sword, by the famine, and by the pestilence.

                            (Ezekiel 6:12)  He that is far off shall die of the pestilence; and he that is near shall fall by the sword; and he that remaineth and is besieged shall die by the famine: thus will I accomplish my fury upon them.

                            (Ezekiel 6:13)  Then shall ye know that I am the LORD, when their slain men shall be among their idols round about their altars, upon every high hill, in all the tops of the mountains, and under every green tree, and under every thick oak, the place where they did offer sweet savour to all their idols.

                            (Ezekiel 6:14)  So will I stretch out my hand upon them, and make the land desolate, yea, more desolate than the wilderness toward Diblath, in all their habitations: and they shall know that I am the LORD.



                            (Ezekiel 7:1)  Moreover the word of the LORD came unto me, saying,

                            (Ezekiel 7:2)  Also, thou son of man, thus saith the Lord GOD unto the land of Israel; An end, the end is come upon the four corners of the land.

                            (Ezekiel 7:3)  Now is the end come upon thee, and I will send mine anger upon thee, and will judge thee according to thy ways, and will recompense upon thee all thine abominations.

                            (Ezekiel 7:4)  And mine eye shall not spare thee, neither will I have pity: but I will recompense thy ways upon thee, and thine abominations shall be in the midst of thee: and ye shall know that I am the LORD.

                            (Ezekiel 7:5)  Thus saith the Lord GOD; An evil, an only evil, behold, is come.

                            (Ezekiel 7:6)  An end is come, the end is come: it watcheth for thee; behold, it is come.

                            (Ezekiel 7:7)  The morning is come unto thee, O thou that dwellest in the land: the time is come, the day of trouble is near, and not the sounding again of the mountains.

                            (Ezekiel 7:8)  Now will I shortly pour out my fury upon thee, and accomplish mine anger upon thee: and I will judge thee according to thy ways, and will recompense thee for all thine abominations.

                            (Ezekiel 7:9)  And mine eye shall not spare, neither will I have pity: I will recompense thee according to thy ways and thine abominations that are in the midst of thee; and ye shall know that I am the LORD that smiteth.



                            (Ezekiel 9:4)  And the LORD said unto him, Go through the midst of the city, through the midst of Jerusalem, and set a mark upon the foreheads of the men that sigh and that cry for all the abominations that be done in the midst thereof.

                            (Ezekiel 9:5)  And to the others he said in mine hearing, Go ye after him through the city, and smite: let not your eye spare, neither have ye pity:

                            (Ezekiel 9:6)  Slay utterly old and young, both maids, and little children, and women: but come not near any man upon whom is the mark; and begin at my sanctuary. Then they began at the ancient men which were before the house.

                            (Ezekiel 9:7)  And he said unto them, Defile the house, and fill the courts with the slain: go ye forth. And they went forth, and slew in the city.

                            (Ezekiel 9:8)  And it came to pass, while they were slaying them, and I was left, that I fell upon my face, and cried, and said, Ah Lord GOD! wilt thou destroy all the residue of Israel in thy pouring out of thy fury upon Jerusalem?

                            (Ezekiel 9:9)  Then said he unto me, The iniquity of the house of Israel and Judah is exceeding great, and the land is full of blood, and the city full of perverseness: for they say, The LORD hath forsaken the earth, and the LORD seeth not.



                            (Ezekiel 22:19)  Therefore thus saith the Lord GOD; Because ye are all become dross, behold, therefore I will gather you into the midst of Jerusalem.

                            (Ezekiel 22:20)  As they gather silver, and brass, and iron, and lead, and tin, into the midst of the furnace, to blow the fire upon it, to melt it; so will I gather you in mine anger and in my fury, and I will leave you there, and melt you.

                            (Ezekiel 22:21)  Yea, I will gather you, and blow upon you in the fire of my wrath, and ye shall be melted in the midst thereof.

                            (Ezekiel 22:22)  As silver is melted in the midst of the furnace, so shall ye be melted in the midst thereof; and ye shall know that I the LORD have poured out my fury upon you.



                            (Ezekiel 36:18)  Wherefore I poured my fury upon them for the blood that they had shed upon the land, and for their idols wherewith they had polluted it:



                            (Ezekiel 38:18)  And it shall come to pass at the same time when Gog shall come against the land of Israel, saith the Lord GOD, that my fury shall come up in my face.

                            (Ezekiel 38:19)  For in my jealousy and in the fire of my wrath have I spoken, Surely in that day there shall be a great shaking in the land of Israel;



                            (Nahum 1:2)  God is jealous, and the LORD revengeth; the LORD revengeth, and is furious; the LORD will take vengeance on his adversaries, and he reserveth wrath for his enemies.



                            (Zephaniah 1:17)  And I will bring distress upon men, that they shall walk like blind men, because they have sinned against the LORD: and their blood shall be poured out as dust, and their flesh as the dung.

                            (Zephaniah 1:18)  Neither their silver nor their gold shall be able to deliver them in the day of the LORD'S wrath; but the whole land shall be devoured by the fire of his jealousy: for he shall make even a speedy riddance of all them that dwell in the land.



                            (Zephaniah 2:2)  Before the decree bring forth, before the day pass as the chaff, before the fierce anger of the LORD come upon you, before the day of the LORD'S anger come upon you.



                            (Zephaniah 3:8)  Therefore wait ye upon me, saith the LORD, until the day that I rise up to the prey: for my determination is to gather the nations, that I may assemble the kingdoms, to pour upon them mine indignation, even all my fierce anger: for all the earth shall be devoured with the fire of my jealousy.



                            (Matthew 10:35)  For I-came to-bisect; (a) MAN against his father, and (a) daughter against her mother, and (a) bride against her mother-in-law.



                            John 3:16 For thus the God cherished the world so-that he-gave his son… cherished is past tense not present or future.



                            (John 3:36) The (one) trusting with-reference-to the son is-having life eternal; but the (one) disobeying to-the son will not see life, BUT the wrath of-the God is-remaining on him.



                            (John 9:31) But we-are-knowing-absolutely that the God is not hearing of-sinners; BUT if any-one might-be God-pious and he-might-be-doing his will, he-is-hearing of-this (one).



                            (Romans 1:18)  For wrath of-God is-being-uncovered on all impiety and unrighteousness of-MEN, the (ones) holding-fast the truth in unrighteousness,



                            (Romans 11:22)  See therefore graciousness and severity of-God:  on-the-one-hand on the (ones) having-fallen severity, on-the-other-hand on you graciousness of God, if you-might-continue in-the graciousness, since you yourself also will-be-chopped-away,



                            (Hebrews 12:6) For whom Jehovah is-cherishing he-is-disciplining, but he-is-whipping every son whom he-is-receiving-alongside.



                            (2 Corinthians 5:11) Knowing-absolutely therefore the fear of-the Lord we-are-persuading MEN, but we-have-been-and-still-are-manifested to-God, but I-am-hoping also to-have-been-and-still-be-manifested in YOUR consciences.



                            (2 Thessalonians 1:6) If-altogether (it-is) (a) just-thing beside God to-repay tribulation to-the (ones) oppressing YOU



                            (1 John 2:15) YOU-be not cherishing the world neither the (things) in the world.  If someone might-be-cherishing the world, the charity of-the Father is not in him;



                            (Revelation 3:19)   As-many-as if I myself might-love I-am-reproving and I-am-disciplining; you-be-zealous therefore and you-repent.



                            (Revelation 6:16) And they-are-saying to-the mountains and to-the rocks:  YOU-fall on us and YOU-hide us from (the) face of-the (one) sitting on the throne and from the wrath of-the Lamb,

                            (Revelation 6:17) Because the day, namely-the great (day) of-his wrath, came and who is-able to-be-stood?



                            (Revelation 14:10) Even he himself-will-drink out-of the wine of-the anger of-the God namely-the (wine) having-been-and-still-mingled undiluted in the cup of-his wrath, and he-will-be-tormented in fire and sulphur in-sight of-holy angels and in-sight of-the lamb.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "Who Chooses The Rules of the World?",
                        tabContent: (
                          <div>
                            <h3>Who Chooses The Rules of the World?</h3>
                            <p>
                            Daniel 4:17  The sentence is by the decree of the watchers, and the demand by the word of the holy ones; to the intent that the living may know that the Most High ruleth in the kingdom of men, and giveth it to whomsoever he will, and setteth up over it the lowest of men.



                            Daniel 4:24-25  ..this is the interpretation, O King, and it is the decree of the Most High, which is come upon my lord the king: that thou shalt be driven from men, and thy dwelling shall be with the beasts of the field, and thou shalt be made to eat grass as oxen, and shalt be wet with the dew of heaven, and seven times shall pass over thee: till thou know that the Most High ruleth in the kingdom of men, and giveth it to whomsoever he will.



                            Daniel 4:32  ..the Most High ruleth in the kingdom of men, and giveth it to whosoever he will.



                            Daniel 4:35   and all the inhabitant of the earth are reputed as nothing; and he doeth according to his will in the army of heaven, and among the inhabitants of the earth; and none can stay his hand, or say unto him, What doest thou?



                            Daniel 5:21 ..and he(Nebuchadnezzar) was driven from the sons of men, and his heart was made like the beasts’, and his dwelling was with the wild asses; he was fed with grass like oxen, and his body was wet with the dew of heaven; until he knew that Most High God ruleth in the kingdom of men, and that he setteth up over it whomsoever he will.



                            Jeremiah 27:5  I have made the earth, the men and the beasts that are upon the face of the earth, by my great power and by my outstretched arm; and I give it unto whom it seemeth right  unto me.



                            Job 12:23-25  He increaseth the nations, and he destroyeth them: He enlargeth the nations, and he leadeth them captive.   He taketh away undertstanding from the chiefs of the people of the earth, and causeth them to wander in a wilderness where there is no way.  They grope in the dark without light: and he maketh them to stagger like a drunken man.



                            Luke 1:52  He-lowered powerful-ones from thrones, and he-raised-to-a-height ones-humble.

                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "Martin Luther (1483 - 1546)",
                        tabContent: (
                          <div>
                            <h3>Martin Luther (1483 - 1546)</h3>
                            <p>
                            Martin Luther has been compared by many to the Apostle Paul as one of the greatest man of the ages.  Remember he was originally Roman Catholic.  Although he objected to some of the things in the “church”, much of his theology was from the Roman Catholic church and extremely anti-Semitic.  The following appears in his writings:



                            …Let me give you my honest advice.



                            First, their synagogues or churches should be set on fire, and whatever does not burn up should be covered or spread over with dirt so that no one may ever be able to see a cinder  or stone of it.  And this ought to be done for the honor of God and of Christianity in order that God may see that we are Christians, and that we have not wittingly tolerated or approved of such public lying, cursing, and blaspheming of His Son and His Christians.



                            Secondly, Their homes should be broken down and destroyed.  For they perpetrated the same things there that they do in their synagogues.  For this reason they ought to be put under one roof or in a stable like gypsies, in order that they may realize that they are not masters in our land, as they boast, but miserable captives, as they complain of us incessantly before God with bitter wailing.



                            Thirdly, they should be deprived of their prayerbooks and Talmuds in which such idolatry, lies, cursing, and blasphemy are taught.



                            Fourthly, their rabbis must be forbidden under threat of death to teach any more.



                            Fifthly, passport and traveling privileges should be absolutely forbidden to the Jews.  For they have no business in the rural districts since they are not nobles, nor officials, nor merchants, nor the like.  Let them stay at home.



                            Sixthly, they ought to be stopped from usury (interest).  All their cash and valuables of silver and gold ought to be taken from them and put aside for safekeeping.  For this reason, as said before everything that they possess they stole and robbed from their usury, for they have no other means of support.  This money should be used in the case (and in no other) where a Jew has honestly become a Christian, so that he may get for the time being one or two or three hundred florins, as the person may require.  This, in order that he may start a business to support his poor wife and children and the old and feeble.  Such evilly required money is cursed, unless, with God’s blessing, it is put to some good and necessary use.



                            Seventhly, let the young and strong Jews and Jewesses be given the flail. The ax, the hoe, the spade, the distaff, and spindle, and let them earn their bread by the sweat of their noses as is enjoined upon Adam’s children.  For it is not proper that they should want us cursed Goyylm to work in the sweat of our brow and that they, pious crew, idle away their days at the fireside in laziness, feasting, and display. And in addition to this, they boast impiously that they have become masters of the Christians at our expense.  We ought to drive the rascally lazy bones out of our system.



                            If, however, we are afraid that they might harm us personally, or our wives, children servants, cattle, etc., when they serve us or work for us - since it is surely to be presumed that such noble lords of the world and poisonous bitter worms are not accustomed to any work and would very unwillingly humble themselves to such a degree among the cursed Goyylm – then let apply the same cleverness [expulsion] as the other nations, such as France, Spain, Bohemia, etc., and settle with them for that which they have extorted usuriously from us, and after having divided it up fairly let us drive them out of the country for all time.  For, as has been said, God’s rage is so great against them that they only become worse and worse through mild mercy, and not much better through severe mercy.  Therefore away with them.



                            To sum up, dear princes and nobles who have Jews in your domains, if this advice of mine does not suit you, then find a better one so that you and we may all be free of this insufferable devilish burden – the Jews.




                            In the night of November 9-10, 1938 the Nazis carried out his advice. This was known as the “Night of the Broken Glass” (Kristalnacht).  Martin Luther apparently had never studied the book of Romans especially chapters 3 and 11.  Romans 3:1 “What therefore the advantage of-the Jews or what the profit of-the circumcision?  2.  Much according-to every manner. For first on-the-one-hand because they-were-trusted with the oracles of-the God”.  Romans 11: 1. “ I-am-saying therefore, Has the God pushed-away-from-himself his people? No! May-it-not-come-to-pass; for I myself also am an Israelite, out-of seed of-Abraham, of-the-tribe of-Benjamin.  2.  The God has not pushed-away-from-himself his people whom he-came-to-know-before”.



                            When you read those verses, how can there be any question as to who the Gods people are and have been.  Joel 3:2  “I will gather all nations, and will bring them down into the valley of Jehoshaphat; and I will execute judgement upon them there for my people and for my heritage Israel, whom they have scattered among the nations: and they have parted my land”.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: 'The Great Commission "Go Ye . . . "',
                        tabContent: (
                          <div>
                            <h3>The Great Commission "Go Ye . . . "</h3>
                            <p>
                            How many times have you heard Matthew 28:19 and Mark 16:15 quoted?  “Go ye therefore, and teach all nations, baptizing them in the name of the Father, and of the Son, and of the Holy Ghost.”  Is this really what the Greek states?  Do you realize that over half of the missionaries that go into the field never complete their tour of duty?  Can the Almighty be wrong that many times?



                            There are three words in this verse we need to investigate.  They are Go, Teach, and Nations.



                            The Greek word that is translated “go” in these two verses is poreuomai (poreuomai).  The King James has 21 different Greek verbs all translated “to-go”.  The Greek word poreuomai(poreuomai) in the KJ is translated into eleven (11) different English words as follows: be going-1, depart-11, go-119, go away-1, go forth-1, go ones’ way-7, go up-1, journey-2, make ones’ journey-1, take ones’ journey-1, and walk-9. Not very consistent is it.



                            The form of this verb in these two verses is an aorist passive participle, which literally means, “having proceeded”.  This is not the imperative form that would express a command.  Jesus is talking to the 11 disciples.  The first gentile, Cornelius in Acts 10 has not been saved yet.  Remember, the new covenant does not start until Jesus died on the cross (Hebrews 9:16).  Therefore poreuomai(poreuomai), having proceeded, means  where ever you go make learners.



                            The next word to consider is the Greek word maqhteuw (matheteuo) which only occurs four (4) times in the New Testament.  The KJ has translated this word in Matt. 19:28 and Mark 16:15 teach.  The Greek word for disciple is maqhths (mathetes) and is translated correctly in the KJ 269 times.  The Greek word maqhteuw (matheteuo) should be translated  “ make  disciples”.  The word disciple means  to “make learners”.  The Greek word for teach is didaskw (didasko) and is translated correctly in the KJ.  It is obvious both Greek words can not mean teach and that maqhteuw (matheteuo) means to make disciples.  The KJ translated the Greek words for disciple and teach correctly in other verses, why not in Matt 19:28 and Mark 16:15?



                            The next word to consider is nations.  The Greek word used in these two verses is eqnos (ethnos).  The KJ translates this Greek word several different ways as follows: gentiles-93, heathen-5, nation-64, and people-3.  When the Greek article “the” is used before eqnos (ethnos), it should be translated “gentiles”.  The Greek article is associated with gesture and aids in pointing out like an index finger.  Whenever the Greek article occurs, the object is certainly definite.  This is not just any type of nation but a gentile nation.



                            There are over 4800 Greek words in the New Testament and the article “the” is by far the most important word in the Greek language being used over 17,000 times.  Two times more than any other word.  This word is really abused in the English translations since most translations used the Latin Vulgate as a source in their translations and there is not an article “the” in the Latin language.



                            The correct translation for Matthew 28:19 is:  “Therefore having-proceeded YOU-disciple all the Gentiles baptizing them with-reference-to the name of-the Father and of-the Son and of-the Holy Spirit”.



                            No matter where you go, witness to people.  You don’t have to go to China or Russia to make disciples, most of us have not even talked to our next door neighbor yet.  We can not save souls, only the Holy Spirit can do that.  We are instructed to make disciples or learners.  We need to be careful that what we are teaching is what we have learned that scriptures mean and not what we have been told that they mean.  We are responsible for what we teach.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "Jehovah's Word Concerning Death",
                        tabContent: (
                          <div>
                            <h3>Jehovah's Word Concerning Death</h3>
                            <p>
                            We must all face a period of time when we will leave this earth.  It is the culmination of life here and is extremely important.  Therefore, it would certainly seem that throughout the Word of the God, significant information concerning this particular experience would be found.



              To begin to understand this subject we need to understand those portions of scripture concerning the “transformation of Jesus the Messiah” while He was on the earth.  This experience is recorded three (3) places and it requires reviewing each to understand the subject.  They are Matthew 17, Mark 9, and Luke 9.



              Most English translations translate the Greek word metamorphoom “transfiguration” which is totally wrong.  In fact most English translations say Jesus is transfigured and Satan is transformed (2 Cor. 11:14) which is backwards.  The English word for transform comes from the Greek word metamorphosis and can be described by the butterfly.  When a little, ugly, caterpillar ceases its normal activities it makes a total change from its normal life, it ceases to seek food and begins to weave about itself a cocoon.  When complete the caterpillar is encased in total darkness and stays there approximately two(2) weeks or if this occurs in the fall he stays all winter.  After this time or when the weather begins to warm an opening is made in the end of the cocoon and out comes a beautiful butterfly.  To be transformed means to be changed from one thing to something totally different.  The caterpillar is transformed into a butterfly.  To transfigure something is like transfiguring a Japanese Rock Garden into a Chinese Rock Garden.  Different but similar!!  II Cor.11:13-15 is very interesting!  “13. For the ones such-as-these are false-apostles, treacherous workman, transfiguring-themselves into apostles of-Messiah.  14. And no marvel, for the adversary is-transfiguring-himself into an angel of-light.  15. Therefore it-is not  a great-thing if his ministers also are-transfiguring-themselves as ministers of-justice: of-whom the finish will-be according-to their works.”  Satan and his ministers do this by teaching enough truth that they appear righteous.



              (1) Now lets read Matt. 17:1-3 “1. And after six days the Jesus is-taking-along-with-himself the Peter and James and John his brother, and he-is bring them up into a high mountain privately.  2.And he-was-transformed in-front of-them, and his face shown as the sun, but his garments became white as the light; 3. And behold, Moses and Elijah were-seen by-them speaking-together with him.”  Jesus the Messiah had changed from the Son of man to the Son of God.  His garments became white as the light.



              (2) Now let’s read Mark 9:1-8. “And he-was-saying to-them, Amen I-am-saying to-YOU, that some of-the ones having-stood-and-still-standing here are ones-who by-no-means might-taste to-death till they-might-see the kingdom of-the God having-come in power.  2. And after six days the Jesus is-taking-along-with-him the Peter and the James and the John, and he-is-bringing them up into a high mountain privately alone. And he-was-transformed in-front of-them; 3. And his garment become glistening, very white as snow, such-as a fuller on the earth in not being-able to-whiten,  4.  And Elias together-with Moses was-seen by-them, and they-were speaking-together with-the Jesus.  5. And the Peter having-answered is-saying to-the Jesus, Rabbi, it-is fine for us to-be here, and let-us make three booths, one for-you, and one for-Moses, and one for-Elias.”



              Remember, when Jesus was on the road to Emmaus after He had been stood-again by the Father, they did not know Him because he had received His heavenly body.



              (3) Now let’s read Luke 9:28-32.  “28. And it come-to-pass about eight days after these words and having-taken-along the Peter and John and James he-ascended into the mountain to-pray. 29.  And with him to-be-praying the shape of-his face was different, and his vesture white flashing-out.  30.  And behold, two men were-speaking-together with-him, ones-who were Moses and Elias, 31.  Who having-seen in glory were-saying of-his exodus which he-was-being-about to-be-fulfilling in Jerusalem.  32.  But the Peter and the-ones together-with him were having-been-and-still-weighted with-slumber,  But having-watched-thoroughly they-saw his glory, and the two men, namely-the-ones having-stood-and-still-standing-together-with-him.”  In these verses we learn that Moses and Elias were discussing his exodus.  Most English translations translation the Greek word (exodos) exodus by deceased which implies that Jesus is going to die.  Jesus didn’t talk about His death, but His Exodus from this world.  Jesus the Messiah is God in the flesh.



              As a believer, the Holy Spirit dwells within us since our earthly body is a Tabernacle for the Holy Spirit to dwell in.  When this body ceases, the Spirit returns to the One that gave it to us, the Almighty Himself.  Are we given any understanding about what the trip is like when our time on this earth is up?  Psalms 23:5, “Though we pass through the valley of the shadow of death we shall fear no evil.”  In Hebrews 13:5 we are given a great promise by the Messiah to all, who in truth put their trust in Him. The Messiah tells the believer, “I will never leave you, or forsake you.”.  Therefore, we know that as a believer we do go down into the valley of the shadow of death BUT we are not alone.  The true God will accompany us through this experience.  We are told in scripture that Messiah Jesus tasted death for His own.  Hebrew 2:9 “But the one having-been-made-and-still a certain small-amount less beside angels we-are-looking-to, namely Jesus, because-of the suffering of-the death having-been-and-still-crowned with glory and with-honor in-which-case he-might-taste of-death by-favor of-God in behalf-of every-one.”  He went down in the valley of the shadow of death, and went on through the horrible experience of death that those who truly cherish Him and have put their trust in Him will never taste death!  Matt. 16:28 “Amen I-am-saying to-YOU, there-are some of-the-ones having-stood-and-still-standing here, they-who by-no-means might taste of-death till they-might-see the son of-the-MAN coming in his kingdom.”  John 8:51  “Amen, amen, I-am-saying to-YOU, if someone might-keep the word namely-the mine, by-no-means might- he-observe death with-reference-to the age”.





              We will experience an exodus from this body to the new one HE has for us in the presence of the Eternal God.  We are also told that He went down into the area of death and emerged victorious to become the firstfruit of all believers.  I Cor. 15: 20-23, “20. But at-this-instant Messiah has-been-and-still-is-raised out-of dead ones having-fallen-asleep-and-still-sleep: 21. For since-indeed the death is through MAN, also through MAN a standing-again of-dead ones. 22. For as-altogether in the Adam all are-dying-off, thus also in the Messiah all will-be-made-alive.  23. But each one in His own assignment: firstfruit Messiah, therefore the ones of-the Messiah in his presence,”  Now at the end of a believer’s life span, they can confidently and triumphantly go down into the valley of the shadow of death with no fear of ‘Death Itself’, the Messiah has taken that awful experience and delivered us from it.



              So the point we understand in the departure of a believer is that down in the valley of the shadow of death they may see ‘death itself’, BUT they experience an exodus before actually entering into THE DEATH.  We are told in II Cor. 5:8 that the believer is to be absent from the body is to be present with the Messiah.  This exodus from the earth to be with the Messiah is in the “twinkling of-an eye”.  I Cor. 15:52, “ In a moment in a twinkling of-an eye, in the last trumpet; for a trumpet-will-sound and the dead ones will-stand-again imperishable, and we ourselves-shall-be-changed.”



              What do we know about the place to which the loved one goes?  In I Cor. 2:9 we are told, “BUT according-as it-has-been-and-is-still-written: Things-which eye saw not and ear heard not and upon the heart of-MAN ascended not, things-which the God prepared for the ones cherishing him”.  We simply can not comprehend the place of God’s abode.  Are we told anymore about this place? Yes, II Cor. 12:4, “That he (Paul)-was-seized into the paradise (the third heaven) and he-heard inexpressible sayings, which are not being-legitimate for-MAN to-speak”. The apostle Paul tells of an experience in his lifetime in which he was carried up into the third heaven.  In that we have no vocabulary to deal with the subject, he tells us that it was not possible for him to describe.  We simply have no words.  In the New Testament the word Heaven appears 193 times in the singular and 93 times in the plural.  Very interesting!!



              Do we have any understanding of what the departed ones in Messiah are like in appearance?  In Phil. 3:21 we are told, “Who will-transfigure the body of our humbling conforming it to-the body of his glory, according-to the operation of him being-able also to-subject to-himself [the] all things.  Also, I John 3:1-2,  “YOU-see of-what-quality charity the Father has-given-and-still-gives to-us in-order-that we-might-be-called children of-God, and we-are.  Because-of this the world is not coming-to-know us because it-came not to-know him.  2. Cherished ones, we are now children of-God, and it-was not-yet manifested what we-shall-be.  We-are-knowing absolutely that if he-might-be-manifested we-shall-be like him, because we-shall-see him according-as he-is”.



              The believers heavenly clothing is indescribably more beautiful than anything that could be obtained while in the mortal body.  The attire is now proper for the immortal body, for the kingly court they now inhabit.  Rev. 19:7-8  “7. Let-us-be-rejoicing and let-us-be-exulting, and we-shall-give the glory to-him, because the marriage of-the Lamb came, and his wife prepared herself,  8. And it-was-given to-her in-order-that she-might-cast-around-to herself a clean brilliant-white fine-linen garment; for the fine-lined-garment is the just-acts of-the holy-ones”.  And this is not the believer’s righteousness: Phil. 3:9, “And I-might-be-found in him, not having my justice, the justice out-of law, But the righteousness through trust of-Messiah, the righteousness out-of God upon the trust,”



              What an amazing picture!  When our MESSIAH made His exodus from this earth, He did not bypass the horrible area of DEATH:  No, ‘HE tasted death for all’.  He did this in order that the believer could enter ‘the valley of the shadow of death’ with no fear and not alone.  There, the believer before ‘tasting death’ will exodus their old tabernacle to go immediately into the presence of JEHOVAH, having experienced metamorphous in route.  Psalms 17:15  “As for me, I shall behold thy face in righteousness: I shall be satisfied, when I awake, with beholding thy form”.



              The believer will awake in the presence of the REDEEMER to find that:



                They have the likeness of the TRUE GOD!

                With the likeness of God, they have immortality!

                Forever they will be sinless!

                They are clothed in the righteousness which is of GOD!

                And the believers are a joint inheritor of the entire universe:

                Romans  8:16-17,



              “The Spirit itself is-witnessing-together with our spirit that we-are children of God.  But if children, also heirs; on-the-one-hand heirs of-God, on-the-other-hand heirs-together of-Messiah, if-all-together we-are-suffering-evil-together in-order-that we-might also be-glorified-together”.



              When we believe in and stand up for Jesus Messiah we will experience many tribulations but you will know it was worth it all when you see Jesus Messiah Jehovah!
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "How Many Crosses at the Crucifixion",
                        tabContent: (
                          <div>
                            <h3>How Many Crosses at the Crucifixion</h3>
                            <p>
                            Two Robbers (lēstēs) Reproach Jesus
                            MATT.27v38 Then two robbers are-being-crucified together-with him, one out-of rights and one out-of lefts.
<br />
                            MATT.27v39 But the (ones) proceeding-along were-blaspheming  him moving their heads
<br />
                            MATT.27v40 And saying:  The (one) overthrowing the sanctuary and building-up in three days, you-save-yourself, if you-are son of-the God, and you-descend from the cross.


<br />
                           Two Robbers (lēstēs) Reproach Jesus
<br />
                            MARK15v27 And together-with him they-are-crucifying two robbers, one out-of right[s] and one out-of left[s] of-him.
<br />
                            MARK15v28 And the scripture was-fulfilled, the (one) saying:  And he-was-figured with lawless (ones).
<br />
                            MARK15v29 And the (ones) proceeding-along were-blaspheming him moving their heads and saying: Aha the (one) overthrowing the sanctuary and in three days building-up.
<br />
                            MARK15v30 You-save yourself, and you-descend from the cross.


<br />
                           Two Criminals (kakourgos)  One Asked Jesus For The Kingdom
<br />
                            LUKE23v39 But one of-the criminals having-been-hanged was-blaspheming him, saying:  If you yourself-are the Messiah, you-save yourself and us.
<br />
                            LUKE23v40 But the different (one) having-answered was-rebuking him, saying:  But (are) you yourself not fearing-for-yourself the God, because you-are in the same sentence?
<br />
                            LUKE23v41 And we on-the-one-hand justly; for we-are-taking-back worthy-(things) of-what-(things) we-practised; on-the-other-hand this (one) practised not-one-thing out-of-place.
<br />
                            LUKE23v42 And he-was-saying to-the Jesus: You-be-made-mindful of-me Lord, at-the-time-that you-might-come in to-your kingdom.
<br />
                            LUKE23v43 And the Jesus said to-him: Amen I-am saying to-you, today you-will-be with me in the paradise.


<br />
                           Two Hence and Hence
<br />
                           JOHN19v18 Where-in-which they-crucified him, and with him others two hence and hence, but (in) midst the Jesus.


<br />
                           There were two robbers and two criminals.  The Holy Spirit did not use two

                           different Greek words for no reason.  His word does not lie!
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "What Color Garments Did Jesus Wear the Night He Was Tried?",
                        tabContent: (
                          <div>
                            <h3>What Color Garments Did Jesus Wear the Night He Was Tried?</h3>
                            <p>
                            Pilate could fine no fault with Jesus (John 18:38, Luke 23:4) and when he found that Jesus was not in his jurisdiction he sent Him to Herod (Luke 23:7).  Herod asked Jesus many questions but Jesus would not answer him so Herod and his soldiers mocked Him as King of the Jews.


<br />
              Luke 23:11 “But the Herod together-with his armies having-treated him with-contempt, and having-mocked him, having-cast around him a brillant white esthes  robe he-sent him back to-the Pilate.”

<br />

              Pilate was becoming very concerned about crowd control by this time because it was Passover and there were probably over one million Jews in Jerusalem and he had only approximately 4,000 soldiers.  He really wanted to free Jesus because it was the custom during this time of the year to release a prisoner but the crowd wanted Barabbas, a convicted murder.  Jesus was whipped and scourged several times and Pilate hoped this would be sufficient and he could release Jesus but the crowd wanted Him crucified.

<br />

              John 19:1-3 “Then therefore the Pilate took the Jesus and he whipped him.  And the soldiers having-plaited a crown out-of-thorn-plants they-put it upon his head, and they-cast-around him a purple garment (Himation, a royal garment).  And they-said, Hail, the King of-the Jews; and they-were giving slaps to-him.”

<br />

              Pilate was still trying to free Jesus but the crowd wanted Him crucified. Pilate gives in to the crowd.  Matthew 27:24-26 “but the Pilate having-seen that he-is-profiting not-one-thing, BUT rather a tumult is-coming-to-pass, having-taken water he-washed-off-for-himself the hands over-against the crowd saying, I-am innocent from the blood of-this just-one; YOU yourself-will-see.  And having-answered all the people said, His blood upon us and upon our children.  Then he-released to-them the Barabbas, but having-lashed the Jesus he-gave him over in-order-that he might-be-crucified.”

<br />

              Matthew 27:28  “And having-stripped him they-placed-around to-him a scarlet chlamus.   They mocked Him as King of the Jews.  They spit on Him and hit Him.  Then they stripped Him of the scarlet chlamus.

<br />

              Matthew 27:31 “And then they-mocked him they-stripped off him the chlamus, and they-clothed him in his garments; and they-led him away into to-be crudified.”

<br />

              Scripture does not tell us what color garments Jesus wore when He walked the earth but I personally believe that from what we know about the Tabernacle and High Priest colors it was a blue garment which would point to His deity.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: '"Tongue", "Language" - glossary',
                        tabContent: (
                          <div>
                            <h3>"Tongue", "Language" - glossary</h3>
                            <p>
                            Webster’s Dictionary
<br />
                            Glos.so.la.li.a – An ecstatic or apparently ecstatic utterance of unintelligible speechlike sounds, viewed by some as a manifestation of deep religious experience.
<br />
                            The Greek word glvssa  “glossa” means both “tongue” and “language”; as is also true in English, tongue can mean the organ or the language.
<br />
                            The Bible makes it clear when it should be “tongue” and when it should be “language”.  Whenever glvssa  (glossa) is in the Greek text with the article [the], it should always be translated “the tongue” or “the tongues”.  Further; whenever glvssa (glossa) is in the singular with the word pas, (pas) [“all’ or “every”], it too is “tongue”.  All other cased, glvssa (glossa) should be “language”.
<br />
                            The King James translates glvssa (glossa) tongues fifty (50) times all tongues with no differentiation between tongues and languages.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "Total Years From Creation to Jesus",
                        tabContent: (
                          <div>
                            <h3>Total Years From Creation to Jesus</h3>
                            <br />
                            <Button
                              color="info"
                              size="lg"
                              href={creation}
                            >
                              <i className="fas fa-file" /> View Chart
                            </Button>
                          </div>

                        )
                      },
                      {
                        tabButton: "Mark of The Beast",
                        tabContent: (
                          <div>
                            <h3>The Shroud of Turin</h3>
                            <img src={beast} />
                          </div>

                        )
                      },
                      {
                        tabButton: "The Shroud of Turin",
                        tabContent: (
                          <div>
                            <h3>The Shroud of Turin</h3>
                            <img src={turin} />
                          </div>

                        )
                      },
                      {
                        tabButton: "God Owns the Land",
                        tabContent: (
                          <div>
                            <h3>God Owns the Land</h3>
                            <p>
                            Lev 25:23  And the land shall not be sold in perpetuity; for the land is mine: for ye are strangers and sojourners with me.



                            Psa 50:12  If I were hungry, I would not tell thee; For the world is mine, and the fulness thereof.



                            Deu 32:8  When the Most High gave to the nations their inheritance, When he separated the children of men, He set the bounds of the peoples According to the number of the children of Israel.



                            Deu 32:9  For Jehovah's portion is his people; Jacob is the lot of his inheritance.



                            Psa 24:1  A Psalm of David. The earth is Jehovah's, and the fulness thereof; The world, and they that dwell therein.



                            Gods Promise to Abraham



                            Gen 12:1  Now Jehovah said unto Abram, Get thee out of thy country, and from thy kindred, and from thy father's house, unto the land that I will show thee:



                            Gen 12:7  And Jehovah appeared unto Abram, and said, Unto thy seed will I give this land: and there builded he an altar unto Jehovah, who appeared unto him.



                            Gen 13:14  And Jehovah said unto Abram, after that Lot was separated from him, Lift up now thine eyes, and look from the place where thou art, northward and southward and eastward and westward:



                            Gen 13:15  for all the land which thou seest, to thee will I give it, and to thy seed for ever.



                            Gen 15:18  In that day Jehovah made a covenant with Abram, saying, Unto thy seed have I given this land, from the river of Egypt unto the great river, the river Euphrates:



                            Gen 17:8  And I will give unto thee, and to thy seed after thee, the land of thy sojournings, all the land of Canaan, for an everlasting possession; and I will be their God.



                            Jer 7:7  then will I cause you to dwell in this place, in the land that I gave to your fathers, from of old even for evermore.



                            Psa 105:9  The covenant which he made with Abraham, And his oath unto Isaac,



                            Psa 105:10  And confirmed the same unto Jacob for a statute, To Israel for an everlasting covenant,



                            Psa 105:11  Saying, Unto thee will I give the land of Canaan, The lot of your inheritance;


                            Deu 30:20  to love Jehovah thy God, to obey his voice, and to cleave unto him; for he is thy life, and the length of thy days; that thou mayest dwell in the land which Jehovah sware unto thy fathers, to Abraham, to Isaac, and to Jacob, to give them.



                            Guarantee for Israel’s Final Return


                            Jer 30:3  For, lo, the days come, saith Jehovah, that I will turn again the captivity of my people Israel and Judah, saith Jehovah; and I will cause them to return to the land that I gave to their fathers, and they shall possess it.



                            Deu 4:21  Furthermore Jehovah was angry with me for your sakes, and sware that I should not go over the Jordan, and that I should not go in unto that good land, which Jehovah thy God giveth thee for an inheritance:



                            Deu 4:38  to drive out nations from before thee greater and mightier than thou, to bring thee in, to give thee their land for an inheritance, as at this day.



                            Deu 12:9  for ye are not as yet come to the rest and to the inheritance, which Jehovah thy God giveth thee.



                            Deu 25:19  Therefore it shall be, when Jehovah thy God hath given thee rest from all thine enemies round about, in the land which Jehovah thy God giveth thee for an inheritance to possess it, that thou shalt blot out the remembrance of Amalek from under heaven; thou shalt not forget.



                            Deu 26:1  And it shall be, when thou art come in unto the land which Jehovah thy God giveth thee for an inheritance, and possessest it, and dwellest therein,



                            Deu 30:4  If any of thine outcasts be in the uttermost parts of heaven, from thence will Jehovah thy God gather thee, and from thence will he fetch thee:

                            Deu 30:5  and Jehovah thy God will bring thee into the land which thy fathers possessed, and thou shalt possess it; and he will do thee good, and multiply thee above thy fathers.



                            Deu 31:7  And Moses called unto Joshua, and said unto him in the sight of all Israel, Be strong and of good courage: for thou shalt go with this people into the land which Jehovah hath sworn unto their fathers to give them; and thou shalt cause them to inherit it.



                            Jer 25:5  saying, Return ye now every one from his evil way, and from the evil of your doings, and dwell in the land that Jehovah hath given unto you and to your fathers, from of old and even for evermore;



                            Isa 11:11  And it shall come to pass in that day, that the Lord will set his hand again the second time to recover the remnant of his people, that shall remain, from Assyria, and from Egypt, and from Pathros, and from Cush, and from Elam, and from Shinar, and from Hamath, and from the islands of the sea.

                            Isa 11:12  And he will set up an ensign for the nations, and will assemble the outcasts of Israel, and gather together the dispersed of Judah from the four corners of the earth.



                            Isa 35:10  and the ransomed of Jehovah shall return, and come with singing unto Zion; and everlasting joy shall be upon their heads: they shall obtain gladness and joy, and sorrow and sighing shall flee away.



                            Isa 60:21  Thy people also shall be all righteous; they shall inherit the land for ever, the branch of my planting, the work of my hands, that I may be glorified.



                            Jer 16:14  Therefore, behold, the days come, saith Jehovah, that it shall no more be said, As Jehovah liveth, that brought up the children of Israel out of the land of Egypt;

                            Jer 16:15  but, As Jehovah liveth, that brought up the children of Israel from the land of the north, and from all the countries whither he had driven them. And I will bring them again into their land that I gave unto their fathers.



                            Eze 11:17  Therefore say, Thus saith the Lord Jehovah: I will gather you from the peoples, and assemble you out of the countries where ye have been scattered, and I will give you the land of Israel.



                            Eze 28:25  Thus saith the Lord Jehovah: When I shall have gathered the house of Israel from the peoples among whom they are scattered, and shall be sanctified in them in the sight of the nations, then shall they dwell in their own land which I gave to my servant Jacob.



                            Eze 28:26  And they shall dwell securely therein; yea, they shall build houses, and plant vineyards, and shall dwell securely, when I have executed judgments upon all those that do them despite round about them; and they shall know that I am Jehovah their God.



                            Eze 36:24  For I will take you from among the nations, and gather you out of all the countries, and will bring you into your own land.



                            Amo 9:14  And I will bring back the captivity of my people Israel, and they shall build the waste cities, and inhabit them; and they shall plant vineyards, and drink the wine thereof; they shall also make gardens, and eat the fruit of them.

                            Amo 9:15  And I will plant them upon their land, and they shall no more be plucked up out of their land which I have given them, saith Jehovah thy God.



                            Zec 8:8  and I will bring them, and they shall dwell in the midst of Jerusalem; and they shall be my people, and I will be their God, in truth and in righteousness.



                            A Warning for the Nations


                            Joe 3:2  I will gather all nations, and will bring them down into the valley of Jehoshaphat; and I will execute judgment upon them there for my people and for my heritage Israel, whom they have scattered among the nations: and they have parted my land,



                            Deu 32:41  If I whet my glittering sword, And my hand take hold on judgment; I will render vengeance to mine adversaries, And will recompense them that hate me.

                            Deu 32:42  I will make mine arrows drunk with blood, And my sword shall devour flesh; With the blood of the slain and the captives, From the head of the leaders of the enemy.



                            Eze 36:6  Therefore prophesy concerning the land of Israel, and say unto the mountains and to the hills, to the watercourses and to the valleys, Thus saith the Lord Jehovah: Behold, I have spoken in my jealousy and in my wrath, because ye have borne the shame of the nations:



                            Eze 36:7  therefore thus saith the Lord Jehovah: I have sworn, saying, Surely the nations that are round about you, they shall bear their shame.



                            Oba 1:10  For the violence done to thy brother Jacob, shame shall cover thee, and thou shalt be cut off for ever.



                            Zec 12:8  In that day shall Jehovah defend the inhabitants of Jerusalem: and he that is feeble among them at that day shall be as David; and the house of David shall be as God, as the angel of Jehovah before them.

                            Zec 12:9  And it shall come to pass in that day, that I will seek to destroy all the nations that come against Jerusalem.



                            Lev 25:23  And the land shall not be sold in perpetuity; for the land is mine: for ye are strangers and sojourners with me.



                            Eze 36:5  therefore thus saith the Lord Jehovah: Surely in the fire of my jealousy have I spoken against the residue of the nations, and against all Edom, that have appointed my land unto themselves for a possession with the joy of all their heart, with despite of soul, to cast it out for a prey.





                            A Blessing to the Jewish People


                            Deu 1:35  Surely there shall not one of these men of this evil generation see the good land, which I sware to give unto your fathers,



                            Deu 4:21  Furthermore Jehovah was angry with me for your sakes, and sware that I should not go over the Jordan, and that I should not go in unto that good land, which Jehovah thy God giveth thee for an inheritance:



                            Deu 4:22  but I must die in this land, I must not go over the Jordan; but ye shall go over, and possess that good land.



                            Deu 6:18  And thou shalt do that which is right and good in the sight of Jehovah; that it may be well with thee, and that thou mayest go in and possess the good land which Jehovah sware unto thy fathers,



                            Deu 8:7  For Jehovah thy God bringeth thee into a good land, a land of brooks of water, of fountains and springs, flowing forth in valleys and hills;



                            Deu 8:10  And thou shalt eat and be full, and thou shalt bless Jehovah thy God for the good land which he hath given thee.



                            Deu 9:6  Know therefore, that Jehovah thy God giveth thee not this good land to possess it for thy righteousness; for thou art a stiffnecked people.



                            Deu 11:17  and the anger of Jehovah be kindled against you, and he shut up the heavens, so that there shall be no rain, and the land shall not yield its fruit; and ye perish quickly from off the good land which Jehovah giveth you.



                            Deu 28:3  Blessed shalt thou be in the city, and blessed shalt thou be in the field.



                            Deu 28:4  Blessed shall be the fruit of thy body, and the fruit of thy ground, and the fruit of thy beasts, the increase of thy cattle, and the young of thy flock.



                            Deu 28:5  Blessed shall be thy basket and thy kneading-trough.



                            Deu 28:6  Blessed shalt thou be when thou comest in, and blessed shalt thou be when thou goest out.



                            Deu 28:7  Jehovah will cause thine enemies that rise up against thee to be smitten before thee: they shall come out against thee one way, and shall flee before thee seven ways.



                            Deu 28:8  Jehovah will command the blessing upon thee in thy barns, and in all that thou puttest thy hand unto; and he will bless thee in the land which Jehovah thy God giveth thee.



                            Deu 28:9  Jehovah will establish thee for a holy people unto himself, as he hath sworn unto thee; if thou shalt keep the commandments of Jehovah thy God, and walk in his ways.



                            Deu 28:10  And all the peoples of the earth shall see that thou art called by the name of Jehovah; and they shall be afraid of thee.



                            Deu 28:11  And Jehovah will make thee plenteous for good, in the fruit of thy body, and in the fruit of thy cattle, and in the fruit of thy ground, in the land which Jehovah sware unto thy fathers to give thee.



                            Deu 28:12  Jehovah will open unto thee his good treasure the heavens, to give the rain of thy land in its season, and to bless all the work of thy hand: and thou shalt lend unto many nations, and thou shalt not borrow.



                            Deu 28:13  And Jehovah will make thee the head, and not the tail; and thou shalt be above only, and thou shalt not be beneath; if thou shalt hearken unto the commandments of Jehovah thy God, which I command thee this day, to observe and to do them,
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "IBM and the Holocaust",
                        tabContent: (
                          <div>
                            <h3>IBM and the Holocaust</h3>
                            <img src={iBMHolocaust} />
                          </div>

                        )
                      },
                      {
                        tabButton: "Henry Ford and Israel",
                        tabContent: (
                          <div>
                            <h3>Henry Ford and Israel</h3>
                            <img src={hFordIsrael} />
                          </div>

                        )
                      },
                      {
                        tabButton: "Jehovah Teaching vs. Catholic Teaching",
                        tabContent: (
                          <div>
                            <h3>Jehovah Teaching vs. Catholic Teaching</h3>
                            <p>
                              This is a study that will compare the teachings of the Word of God – the Holy Scriptures – with the teachings of the Roman Catholic Church- the teachings of men.  Truth will prevail, the word of God will stand without any minute alteration when all the works and words of man have passed into nothingness.  The Messiah said in Matt 24:35, Mark 13:31, Luke 20:33, “Heaven and earth will pass away, but My words will not pass away.”



                                The scriptures teach: “the Word is true from the beginning; and every one of Thy righteous judgments endureth forever” Psa 119:160.  The Messiah said, “I AM the way, the truth, and the life, no man cometh to the Father but by Me.”  The Messiah is Truth; His Word is Truth. No teaching of man will survive, no man can approach the Father except though the Messiah and His Word.  Therefore, teachings of men must be submitted to the teachings of the scriptures.   If they pass this test, they are of Jehovah God; if not then they are a lie.  “Sorcerers, idolaters, and all liars shall have their part in the lake which burneth with fire and brimstone, which is the second death” Rev 21:8.



                                In this study, all references will be taken from the Catholic literature.  Scripture will be taken from the Catholic Bible, the Holy Trinity Edition, edited by Rev. John P. O’Connell with the Imprimatur of Samuel Cardinal Stritch, Archbishop of Chicago.  All Roman Catholic teachings are taken from Catholic Publications.  The most frequently quoted work is the Fountain of Catholic Knowledge, published by Brennan Publishing Co., New York, 1899, with the Imprimatur of Michael Augustinus.



                                As we begin this comparison, consider the guidance as found Isa 8:20 “to the teaching and to the testimony: if they speak not according to this Word (the scriptures) surely there is no light for them”.
                            </p>
                          </div>

                        )
                      },
                      {
                        tabButton: "Love - Agape/Philo",
                        tabContent: (
                          <div>
                            <h3>Love - Agape/Philo</h3>
                            <p>Love is one of the most difficult of words to understand. In speaking we might say we love father, mother, wife, husband, children, girlfriend, boyfriend, school, house, dog, cat, or food; and all of these uses, use love in a different way.  The Greek New Testament uses different words to show love for different people and things.  The English translations of the Bible have made a mess of the subject.</p>
                            <Button
                              color="info"
                              size="lg"
                              href={love}
                            >
                              <i className="fas fa-file" /> More Info
                            </Button>
                         </div>

                        )
                      },
                      {
                        tabButton: "Who is a Neighbor?",
                        tabContent: (
                          <div>
                            <h3>Who is a Neighbor?</h3>
                            <p>
                            We hear many times on TV and in general conversation and read in the Bible that we are �to love our neighbor as ourselves�.

              Who is a neighbor?  Is it the guy next door?  How does the Bible define who a neighbor is?

              LUKE10v30 But having-taken (it) up the Jesus said, (A) certain MAN was-descending from Jerusalem into Jericho, and he-fell-into robbers, who also having-stripped him and having-put-upon (him) blows went-away, having-let (him) go reaching half-dead.

              31 But according-to (a) coincidence (a) certain priest was-descending in that way and having-seen him he-went-by-on-the-other-side;

              32 But likewise also (a) Levite, having-come-to-be according-to the place, having-come and having-seen he-went-by-on-the-other-side.

              33 But (a) certain traveling Samaritan came according-to him, and having-seen him he-was-moved-with-compassion,

              34 And having-come-near he-bound-down his wounds, pouring-on oil and wine; but having-mounted him upon (his) own animal he-led him into (an) inn, and he-cared-for him.

              35 And upon the morrow having-come-out having-cast-out two denarii he-gave (them) to-the innkeeper, and he-said to-him, You-care-for him, and whatsoever something you-might-spend-in-addition, I myself-shall-give-back to-you with my to-be-coming-back.

              36 Therefore which of-these three is-seeming to-you to-have-become neighbor of-the-(one) having-fallen-in into the robbers?

              37 But the-(one) said, The-(one) having-done the mercy with him.  The Jesus therefore said to-him, You-be-proceeding, and you yourself-be-doing likewise.



              The Bible tells us the Samaritan was a neighbor but I do not think he lived next door.  I would

              classify the Samaritan as a fellow believer as a result of his actions.  Scripture tells us to cherish

              our enemies.  Cherish is a form of love as we know it but requires action, we should do

               something to help our enemies.  Love is the affection we have for our father and mother,

              husband, children, etc.



              For a better understand of love see the study on �Love� under �Short Bible Studies�.
                            </p>
                          </div>

                        )
                      }
                    ]}
                  />
                </GridItem>
              </GridContainer>
            </div>
          </div>
        </div>
        <Footer />
      </div>
    );
  }
}

export default withStyles(profilePageStyle)(ProfilePage);
