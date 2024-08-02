import React from "react";

const Card = (props) => {
    return (
        <div className="card">
            <img src={props.img} />
            <div className="card-footer">
                <h3>{props.title}</h3>
            </div>
        </div>
    );
}

export default Card;