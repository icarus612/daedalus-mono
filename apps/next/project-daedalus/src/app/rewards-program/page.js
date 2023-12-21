import { Fragment, useEffect, useState } from 'react'
import styles from '../styles/Home.module.css'

export default function Home() {
  const [customerData, setCustomerData] = useState(false);
  useEffect(()=> {
    fetch('api/random-json-generator?amount=33')
      .then((res)=> res.json())
      .then((json)=> setCustomerData(json));
  }, []);
  return customerData && (
    <table>
      <tbody>
      <tr>
        <th>Name</th>
        <th>Total Spent</th>
        <th>Total Points</th>
        {[...Array(180)].map((_, idx)=> <th key={`${idx}`}>{idx % 2 == 0 ? "Dollars spent" : "Total Points"} on day {idx}</th>)}
      </tr> 
      {customerData.users.map((el, idx)=> {
        const {
          name,
          totalSpentDaily,
          totalSpentPast90,
        } = el;
        let totalPoints = [];
        let pointsHTML = totalSpentDaily.map((amount, idx)=> {
          let s = amount < 100 ? amount - 50 : 50;
          if (s < 0) s = 0;
          let d = amount > 100 && ((amount - 100) * 2);
          let points = s + d;
          totalPoints.push(points);
          return (
            <Fragment key={`${idx}`}>
              <th>${amount || 0}</th>
              <th>{points}</th>      
            </Fragment>
          );
        });
        return (
          <tr key={`${idx}`}>
            <th>{name}</th>
            <th>${totalSpentPast90}</th>
            <th>{totalPoints.reduce((a, b)=> a + b)}</th>
            {pointsHTML}
          </tr>
        );
      })}
      </tbody>
    </table>
  );
}
