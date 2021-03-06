
#include "osj_svd.h"

using std::endl;

//

OSJ_SVD::OSJ_SVD(uint32_t rows, uint32_t cols) : SVD_IF(rows, cols)
{
	if (rows < cols) {
		m_tr = true;
		m_U = MatrixXd(cols, rows);
	}
	else {
		m_tr = false;
		m_U = MatrixXd(rows, cols);
	}

	m_S = VectorXd(m_U.cols());

	m_V = MatrixXd(m_U.cols(), m_U.cols());
}

void OSJ_SVD::initMats(MatrixXd_IN G)
{
	if (m_tr) {
		m_U = G.transpose();
	}
	else {
		m_U = G;
	}
	m_V.setIdentity();
}

bool OSJ_SVD::applyJacobiRot(uint32_t c1, uint32_t c2)
{
	double a = m_U.col(c1).squaredNorm();
	double b = m_U.col(c2).squaredNorm();
	double d = m_U.col(c1).dot(m_U.col(c2));

	bool converged = (d * d <= m_tol_cnv2 * a * b);

	if (!converged) {
		double zeta = (b - a) / (2.0 * d);
		double t;
		if (zeta > 0) t = 1.0 / (zeta + sqrt(1 + zeta * zeta));
		else          t = -1.0 / (-zeta + sqrt(1 + zeta * zeta));
		double c = 1.0 / sqrt(1.0 + t * t);
		double s = c * t;

		VectorXd tmp;
		
		tmp = m_U.col(c1);
		m_U.col(c1) = c * tmp - s * m_U.col(c2);
		m_U.col(c2) = s * tmp + c * m_U.col(c2);

		tmp = m_V.col(c1);
		m_V.col(c1) = c * tmp - s * m_V.col(c2);
		m_V.col(c2) = s * tmp + c * m_V.col(c2);
	}

	return converged;
}

void OSJ_SVD::normSingular(void)
{
	uint32_t n = m_U.cols();

	for (uint32_t i = 0; i < n; i++) {
		double s = m_U.col(i).norm();
		m_S(i) = s;

		if ((-m_tol_div0 < s) && (s < m_tol_div0)) continue;

		m_U.col(i).normalize();
	}
}

void OSJ_SVD::do_decomp(MatrixXd_IN G)
{
	initMats(G);

	uint32_t m = m_U.rows();
	uint32_t n = m_U.cols();

	m_iters = 0;
	bool converged_all;
	do {
		converged_all = true;

		for (uint32_t i = 0; i < n - 1; i++) {
			for (uint32_t j = i + 1; j < n; j++) {
				if (!applyJacobiRot(i, j)) converged_all = false;
			}
		}

		m_iters++;
	} while (!converged_all);

	normSingular();
}

bool OSJ_SVD::do_selftest(MatrixXd_IN G, ostream &out)
{
	MatrixXd Gr;
	if (m_tr) Gr = m_V * m_S.asDiagonal() * m_U.transpose();
	else Gr = m_U * m_S.asDiagonal() * m_V.transpose();

	MatrixXd UtU;
	UtU = m_U.transpose() * m_U;
	MatrixXd VVt;
	VVt = m_V * m_V.transpose();

	out << endl;
	out << "--- G" << endl << G << endl;
	out << endl;
	out << "--- tr" << endl << m_tr << endl;
	out << "--- U" << endl << m_U << endl;
	out << "--- S" << endl << m_S << endl;
	out << "--- V" << endl << m_V << endl;
	out << endl;
	out << "--- G reconstructed" << endl << Gr << endl;
	out << "--- U' * U" << endl << UtU << endl;
	out << "--- V * V'" << endl << VVt << endl;

	Gr -= G;
	double rmseG = Gr.squaredNorm() / Gr.size();
	out << "--- rmseG" << endl << rmseG << endl;

	UtU.diagonal().setZero();
	double rmseU = UtU.squaredNorm() / UtU.size();
	out << "--- rmseU" << endl << rmseU << endl;

	VVt.diagonal().setZero();
	double rmseV = VVt.squaredNorm() / VVt.size();
	out << "--- rmseV" << endl << rmseV << endl;

	return ((rmseG < m_tol_rmse) && (rmseU < m_tol_rmse) && (rmseV < m_tol_rmse));
}

void OSJ_SVD::do_solve(VectorXd_IO x, VectorXd_IN h)
{
	VectorXd Sinv = m_S.cwiseInverse();
	for (Eigen::Index i = 0; i < Sinv.size(); i++) {
		if ((-m_tol_sinv < m_S(i)) && (m_S(i) < m_tol_sinv)) Sinv(i) = 0;
	}

	if (m_tr) x = m_U * (Sinv.asDiagonal() * (m_V.transpose() * h));
	else x = m_V * (Sinv.asDiagonal() * (m_U.transpose() * h));
}
