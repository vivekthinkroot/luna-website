
import { useLocation, useParams } from 'react-router';
import Login from '../components/login';

export default function PricingPage() {
    const url = useLocation();
    const section = url?.pathname?.split('/')[1]
    console.log('route: ', section)
    switch (section) {
        case 'login':
            return <Login/>;
        default:
            return <div>Section not found</div>;
    }
}
