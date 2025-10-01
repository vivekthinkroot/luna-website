
import { useLocation, useParams } from 'react-router';
import Kundli from '../components/KundliPage';

export default function PricingPage() {
    const url = useLocation();
    const section = url?.pathname?.split('/')[1]
    console.log('route: ', section)
    switch (section) {
        case 'kundli':
            return <Kundli/>;
        default:
            return <div>Section not found</div>;
    }
}
