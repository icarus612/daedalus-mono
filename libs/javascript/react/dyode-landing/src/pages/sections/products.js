import React, { useEffect } from "react";
import Flickity from 'flickity';
import ProductImage from '../../assets/images/ProductImage1.jpg';

const Products = () => {

    useEffect(()=> {
        let flkty = new Flickity('.products-flickity', {
            wrapAround: true,
            pageDots: false,
            cellAlign: 'left',
            setGallerySize: false,
            draggable: true,
            lazyLoad: 2
        });
    });
    let flickityGal = [];
    for (let i = 0; i < 10; i++) {
        flickityGal.push(
            <div key={i} className="product-cell">
                <img src={ProductImage} />
                <div className="product-cell-footer">
                    <p className="product-title">
                        Product Title
                    </p>
                    <p>
                        Women's T-Shirt
                    </p>
                    <h5 className="pacifico green">
                        $19.99
                    </h5>
                </div>
            </div>
        )
    }
    return (
        <section className="products container">
            <h2>New Arrivals</h2>
            <div className="products-flickity">
                {flickityGal.map((i)=> i)}
            </div>
        </section>
    );
}

export default Products;