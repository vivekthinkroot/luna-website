
import { useLocation, useParams } from 'react-router';
import Pricing from '../components/Pricing';

export default function PricingPage() {
    const url = useLocation();
    const section = url?.pathname?.split('/')[1]
    console.log('route: ', section)
    switch (section) {
        case 'pricing':
            return <Pricing />;
        default:
            return <div>Section not found</div>;
    }
}
