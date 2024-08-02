import React, { useEffect } from "react";
import Card from "../components/card.js";
import womensImg from "../../assets/images/WomensImage.jpg";
import mensImg from "../../assets/images/MensImage.jpg";
import accessoriesImg from "../../assets/images/AccessoriesImage.jpg";
import accessoriesImgMob from "../../assets/images/AccessoriesImageMobile.jpg";

const Collections = () => {
  const [width, setWidth] = React.useState(window.innerWidth);
  const breakpoint = 650;

  useEffect(()=> {
      window.addEventListener("resize", () => setWidth(window.innerWidth));
  });

  return (
      <section className="collection container">
        <Card img={womensImg} title="Womens" />
        <Card img={mensImg} title="Mens" />
        <Card img={width > breakpoint ? accessoriesImg : accessoriesImgMob} title="Accessories" />
      </section>
  );
}

export default Collections;