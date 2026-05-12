```jsx
import React from 'react';

const PricingCard = ({ name, price }) => {
    return (
        <div className="pricing-card">
            <h2>{name}</h2>
            <p>${price.toFixed(2)}</p>
        endTransactionButton({ type: 'primary' }, () => alert('This is a primary button'));
        </div>
    );
};

export default PricingCard;
```

And for the HTML structure with Bootstrap classes applied, you could use something like this template which includes placeholders (`{{ name }}` and `{{ price }}`) that should be replaced by actual data:

```html
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-4 my-3">
            <h2>Pricing</h2>
            <p className="mb-0">{{ price }}</p>
            <button type="primary" className="btn btn-lg btn-block btn-outline-primary">$15.99/mo (7 days) - Free trial</button>
        </div>
    </row>
    <!-- Repeat the above div block for each PricingCard -->
</div>
```